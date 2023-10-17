import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from steamship import Block, File

from utils.tags import CharacterTag, QuestIdTag, TagKindExtensions


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
                    last_appended[1] = f"{last_appended[1]} && {included[1]}"
                else:
                    result.append(included)
        return result
