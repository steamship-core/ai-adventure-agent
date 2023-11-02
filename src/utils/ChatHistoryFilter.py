import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from steamship import Block, File, Tag
from steamship.agents.schema.message_selectors import tokens
from steamship.data.tags.tag_constants import RoleTag, TagKind, TagValueKey
from steamship.data.tags.tag_utils import get_tag, get_tag_value_key

from schema.game_state import GameState
from utils.moderation_utils import is_block_excluded
from utils.tags import (
    CharacterTag,
    InstructionsTag,
    QuestIdTag,
    QuestTag,
    TagKindExtensions,
)


class ChatHistoryFilter(ABC):
    @abstractmethod
    def filter_blocks(
        self, chat_history_file: File
    ) -> List[Tuple[Block, Optional[str]]]:
        """Returns a list of included blocks, and optional explanations of why included for debugging"""
        pass

    def filter_chat_history(
        self, chat_history_file: File, filter_for: Optional[str] = None
    ) -> List[int]:
        filtered_blocks = self.filter_blocks(chat_history_file=chat_history_file)
        filtered_blocks.sort(key=lambda x: x[0].index_in_file)
        filtered_blocks = [
            block_tuple
            for block_tuple in filtered_blocks
            if (not is_block_excluded(block_tuple[0]) and block_tuple[0].text)
        ]

        debug_messages = [f"{filter_for} input: "]
        for _, (block, inclusion_reason) in enumerate(filtered_blocks):
            debug_messages.append(
                f"{block.index_in_file} [{inclusion_reason}] {block.text}"
            )
        logging.debug("\n".join(debug_messages))
        return [filtered_block[0].index_in_file for filtered_block in filtered_blocks]


class TagFilter(ChatHistoryFilter):
    tag_types: List[Tuple[str, str]]  # Tag names and kinds that should be included

    def __init__(self, tag_types: List[Tuple[str, str]]):
        self.tag_types = tag_types

    def filter_blocks(
        self, chat_history_file: File
    ) -> List[Tuple[Block, Optional[str]]]:
        result: List[Tuple[Block, Optional[str]]] = []
        for block in chat_history_file.blocks:
            for tag in block.tags:
                for (kind, name) in self.tag_types:
                    if tag.kind == kind and tag.name == name:
                        result.append((block, f"{tag.kind} {tag.name}"))
        return result


class QuestNameFilter(ChatHistoryFilter):
    quest_name: str

    def __init__(self, quest_name: str):
        self.quest_name = quest_name

    def filter_blocks(
        self, chat_history_file: File
    ) -> List[Tuple[Block, Optional[str]]]:
        result: List[Tuple[Block, Optional[str]]] = []
        for block in chat_history_file.blocks:
            for tag in block.tags:
                if QuestIdTag.matches(tag, self.quest_name):
                    result.append((block, "Quest ID match"))
        return result


class LastInventoryFilter(ChatHistoryFilter):
    def filter_blocks(
        self, chat_history_file: File
    ) -> List[Tuple[Block, Optional[str]]]:
        result: List[Tuple[Block, Optional[str]]] = []
        for _, block in enumerate(chat_history_file.blocks):
            for tag in block.tags:
                if (
                    tag.kind == TagKindExtensions.CHARACTER
                    and tag.name == CharacterTag.INVENTORY
                ):
                    result = [(block, "Last inventory")]
        return result


class UnionFilter(ChatHistoryFilter):
    filters: List[ChatHistoryFilter]

    def __init__(self, filters: List[ChatHistoryFilter]):
        self.filters = filters

    def filter_blocks(
        self, chat_history_file: File
    ) -> List[Tuple[Block, Optional[str]]]:
        all_results: List[Tuple[Block, Optional[str]]] = []
        for filter in self.filters:
            all_results.extend(
                filter.filter_blocks(chat_history_file=chat_history_file)
            )
        return self.dedupe_results(all_results)

    def dedupe_results(
        self, input: List[Tuple[Block, Optional[str]]]
    ) -> List[Tuple[Block, Optional[str]]]:
        input.sort(key=lambda x: x[0].index_in_file)
        result: List[Tuple[Block, Optional[str]]] = []
        for included in input:
            if len(result) == 0:
                result.append(included)
            else:
                last_appended = result[-1]
                if last_appended[0].index_in_file == included[0].index_in_file:
                    result[-1] = (
                        last_appended[0],
                        f"{last_appended[1]} && {included[1]}",
                    )
                else:
                    result.append(included)
        return result


class TrimmingStoryContextFilter(ChatHistoryFilter):
    def __init__(
        self,
        base_filter: ChatHistoryFilter,
        current_quest_id: str,
        game_state: GameState,
        max_tokens: int,
    ):
        self._base_filter = base_filter
        self._current_quest_id = current_quest_id
        self._game_state = game_state
        self._max_tokens = max_tokens

    def _calculate_and_store_token_count(self, block: Block) -> int:
        if not block.text:
            return 0
        if value := get_tag_value_key(
            block.tags, key=TagValueKey.NUMBER_VALUE, kind=TagKind.TOKEN_COUNT
        ):
            return value
        block_tokens = tokens(block)
        if block.client and block.id:
            tag = Tag.create(
                block.client,
                file_id=block.file_id,
                block_id=block.id,
                kind=TagKind.TOKEN_COUNT,
                value={TagValueKey.NUMBER_VALUE: block_tokens},
            )
        else:
            tag = Tag(
                kind=TagKind.TOKEN_COUNT,
                value={TagValueKey.NUMBER_VALUE: block_tokens},
            )
        block.tags.append(tag)
        return block_tokens

    def filter_blocks(  # noqa: C901
        self, chat_history_file: File
    ) -> List[Tuple[Block, Optional[str]]]:
        block_tuples = self._base_filter.filter_blocks(
            chat_history_file=chat_history_file
        )

        # drop the unwanted ones
        block_tuples = [
            block_tuple
            for block_tuple in block_tuples
            if (not is_block_excluded(block_tuple[0]) and block_tuple[0].text)
        ]

        id_to_reasons = {t[0].id: t[1] for t in block_tuples}
        blocks = [t[0] for t in block_tuples]

        total_tokens = 0

        # MUST include onboarding message, as it provides the proper overall context.
        selected_blocks = []
        for block in blocks:
            if get_tag(
                tags=block.tags,
                kind=TagKindExtensions.INSTRUCTIONS,
                name=InstructionsTag.ONBOARDING,
            ):
                logging.debug(
                    f"Selecting block: ({block.index_in_file}) [{block.chat_role}] {block.text}"
                )
                selected_blocks.append(block)
                total_tokens += self._calculate_and_store_token_count(block)
                logging.debug(f"Total tokens: {total_tokens }")
                break

        # Also, MUST include quest beginning prompt
        for block in reversed(blocks):
            if not get_tag(
                tags=block.tags,
                kind=TagKindExtensions.INSTRUCTIONS,
                name=InstructionsTag.QUEST,
            ):
                continue
            if value := get_tag_value_key(
                tags=block.tags,
                kind=TagKindExtensions.QUEST,
                name=QuestTag.QUEST_ID,
                key="id",
            ):
                if value == self._current_quest_id:
                    logging.debug(
                        f"Selecting block: ({block.index_in_file}) [{block.chat_role}] {block.text}"
                    )
                    selected_blocks.append(block)
                    total_tokens += self._calculate_and_store_token_count(block)
                    logging.debug(f"Total tokens: {total_tokens}")
                    break

        # Now include any assistant/user messages that provide the context.
        for block in reversed(blocks):
            if block.chat_role not in [RoleTag.ASSISTANT, RoleTag.USER]:
                continue
            if value := get_tag_value_key(
                tags=block.tags,
                kind=TagKindExtensions.QUEST,
                name=QuestTag.QUEST_ID,
                key="id",
            ):
                if value == self._current_quest_id:
                    if total_tokens < self._max_tokens:
                        block_tokens = self._calculate_and_store_token_count(block)
                        if block_tokens + total_tokens < self._max_tokens:
                            logging.debug(
                                f"Selecting block: ({block.index_in_file}) [{block.chat_role}] {block.text}"
                            )
                            selected_blocks.append(block)
                            total_tokens += block_tokens
                            logging.debug(f"Total tokens: {total_tokens}")

        if total_tokens < self._max_tokens:
            for block in reversed(blocks):
                if not get_tag(
                    tags=block.tags,
                    kind=TagKindExtensions.QUEST,
                    name=QuestTag.QUEST_SUMMARY,
                ):
                    continue
                if total_tokens < self._max_tokens:
                    block_tokens = self._calculate_and_store_token_count(block)
                    if block_tokens + total_tokens < self._max_tokens:
                        logging.debug(
                            f"Selecting block: ({block.index_in_file}) [{block.chat_role}] {block.text}"
                        )
                        selected_blocks.append(block)
                        total_tokens += block_tokens
                        logging.debug(f"Total tokens: {total_tokens}")

        logging.debug(f"TOTAL_TOKENS = {total_tokens}, MAX_TOKENS = {self._max_tokens}")
        block_list = sorted(selected_blocks, key=lambda b: b.index_in_file)
        return_tuples = []
        for block in block_list:
            return_tuples.append((block, id_to_reasons.get(block.id)))
        return return_tuples
