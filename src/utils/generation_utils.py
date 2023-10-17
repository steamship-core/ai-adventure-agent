"""
Like context_utils, this is meant to provide a light-weight set of utilities.

The goal is to enable the game designer work in a high signal-to-noise environment, like this:

    send_background_music("description", context)
    send_assistant_message("Hi there!", context)

While at the same time not committing to any huge abstraction overhead: this is just a light-weight set of helper
functions whose mechanics can change under the hood as we discover better ways to do things, and the game developer
doesn't need to know.
"""
import time
from typing import List, Optional, Tuple

from steamship import Block, File, Tag
from steamship.agents.schema import AgentContext
from steamship.data import TagKind
from steamship.data.block import StreamState
from steamship.data.tags.tag_constants import ChatTag, RoleTag, TagValueKey

from schema.characters import HumanCharacter
from utils.ChatHistoryFilter import QuestNameFilter, UnionFilter, TagFilter, LastInventoryFilter, ChatHistoryFilter
from utils.context_utils import (
    emit,
    get_audio_narration_generator,
    get_story_text_generator,
)
from utils.tags import (
    AgentStatusMessageTag,
    CharacterTag,
    MerchantTag,
    QuestIdTag,
    QuestTag,
    StoryContextTag,
    TagKindExtensions,
)


def send_audio_narration(block: Block, context: AgentContext) -> Optional[Block]:
    """Generates and sends a background image to the player."""
    generator = get_audio_narration_generator(context)
    task = generator.generate(
        text=block.text,
        make_output_public=True,
        # streaming=True,
    )

    # TODO: Figure out how to do this in a way that's treaming friendly AND sync friendly
    task.wait()
    block = task.output.blocks[0]
    emit(output=block, context=context)
    return block


def send_agent_status_message(
    name: AgentStatusMessageTag, context: AgentContext, value: Optional[dict] = None
) -> Optional[Block]:
    block = Block(
        text="",
        tags=[
            Tag(kind=TagKind.ROLE, name="status-message", value=value),
            Tag(kind=TagKind.AGENT_STATUS_MESSAGE, name=name.value, value=value),
        ],
    )
    emit(block, context=context)
    return block


def send_story_generation(
    prompt: str, quest_name: str, context: AgentContext
) -> Optional[Block]:
    """Generates and sends a background image to the player."""
    block = do_generation(
        context,
        prompt,
        prompt_tags=[Tag(kind=TagKindExtensions.QUEST, name=QuestTag.QUEST_PROMPT), QuestIdTag(quest_name)],
        output_tags=[Tag(kind=TagKindExtensions.QUEST, name=QuestTag.QUEST_CONTENT), QuestIdTag(quest_name)],
        filter=UnionFilter(
            [TagFilter(tag_types = [
                (TagKindExtensions.CHARACTER, CharacterTag.NAME),
                (TagKindExtensions.CHARACTER, CharacterTag.MOTIVATION),
                (TagKindExtensions.CHARACTER, CharacterTag.DESCRIPTION),
                (TagKindExtensions.CHARACTER, CharacterTag.BACKGROUND),
                (TagKindExtensions.STORY_CONTEXT, StoryContextTag.GENRE),
                (TagKindExtensions.STORY_CONTEXT, StoryContextTag.TONE),
                (TagKindExtensions.QUEST, QuestTag.QUEST_SUMMARY),
            ]),
            QuestNameFilter(quest_name=quest_name),
            LastInventoryFilter()
            ]),
        generation_for="Quest Content"
    )
    return block


def generate_quest_summary(quest_name: str, context: AgentContext) -> Optional[Block]:
    """Generates and sends a background image to the player."""
    prompt = "Please summarize the above quest in one to two sentences."
    block = do_generation(
        context,
        prompt,
        prompt_tags=[Tag(kind=TagKindExtensions.QUEST, name=QuestTag.QUEST_PROMPT), QuestIdTag(quest_name)],
        output_tags=[Tag(kind=TagKindExtensions.QUEST, name=QuestTag.QUEST_SUMMARY), QuestIdTag(quest_name)],
        filter=QuestNameFilter(quest_name=quest_name),
        generation_for="Quest Summary"
    )
    return block


def generate_quest_item(
    quest_name: str, player: HumanCharacter, context: AgentContext
) -> (str, str):
    """Generates a found item from a quest, returning a tuple of its name and description"""
    prompt = f"What object or item did {player.name} find during that story? It should fit the setting of the story and help {player.motivation} achieve their goal. Please respond only with ITEM NAME: <name> ITEM DESCRIPTION: <description>"
    block = do_generation(
        context,
        prompt,
        prompt_tags=[Tag(kind=TagKindExtensions.QUEST, name=QuestTag.ITEM_GENERATION_PROMPT),QuestIdTag(quest_name)],
        output_tags=[Tag(kind=TagKindExtensions.QUEST, name=QuestTag.ITEM_GENERATION_CONTENT),QuestIdTag(quest_name)],
        filter=UnionFilter([
            QuestNameFilter(quest_name=quest_name),
            LastInventoryFilter()
            ]),
        generation_for="Quest Item"
    )
    parts = block.text.split("ITEM DESCRIPTION:")
    if len(parts) == 2:
        name = parts[0].replace("ITEM NAME:", "").strip()
        description = parts[1].strip()
    else:
        name = block.text.strip()
        description = ""
    return name, description


def generate_merchant_inventory(
    player: HumanCharacter, context: AgentContext
) -> List[Tuple[str, str]]:
    """Generates the inventory for a merchant"""
    prompt = f"Please list 5 objects that a merchant might sell {player.name} in a shop. They should fit the setting of the story and help {player.motivation} achieve their goal. Please respond only with ITEM NAME: <name> ITEM DESCRIPTION: <description>"
    block = do_generation(
        context,
        prompt,
        prompt_tags=[Tag(
                kind=TagKindExtensions.MERCHANT,
                name=MerchantTag.INVENTORY_GENERATION_PROMPT,
            )],
        output_tags=[Tag(kind=TagKindExtensions.MERCHANT, name=MerchantTag.INVENTORY)],
        filter=UnionFilter([
            TagFilter([
            (TagKindExtensions.CHARACTER, CharacterTag.NAME),
            (TagKindExtensions.CHARACTER, CharacterTag.MOTIVATION),
            (TagKindExtensions.CHARACTER, CharacterTag.DESCRIPTION),
            (TagKindExtensions.CHARACTER, CharacterTag.BACKGROUND),
            (TagKindExtensions.STORY_CONTEXT, StoryContextTag.GENRE),
            (TagKindExtensions.STORY_CONTEXT, StoryContextTag.TONE),
            (TagKindExtensions.QUEST, QuestTag.QUEST_SUMMARY),
            (TagKindExtensions.MERCHANT, MerchantTag.INVENTORY_GENERATION_PROMPT),
            ]), LastInventoryFilter()
        ]),
        generation_for="Merchant Inventory"
    )
    result = []
    items = block.text.split("ITEM NAME:")
    for item in items:
        if len(item.strip()) > 0:
            parts = item.split("ITEM DESCRIPTION:")
            if len(parts) == 2:
                name = parts[0].replace("ITEM NAME:", "").strip()
                description = parts[1].strip()
            else:
                name = item.strip()
                description = ""
            result.append((name, description))
    return result


def do_generation(
    context: AgentContext,
    prompt: str,
    prompt_tags: List[Tag],
    output_tags: List[Tag],
    filter: ChatHistoryFilter,
    generation_for: str, # For debugging output
) -> Block:
    """Generates the inventory for a merchant"""

    generator = get_story_text_generator(context)

    output_tags.extend([
        Tag(
            kind=TagKind.CHAT,
            name=ChatTag.ROLE,
            value={TagValueKey.STRING_VALUE: RoleTag.ASSISTANT},
        ),
        Tag(kind=TagKind.CHAT, name=ChatTag.MESSAGE),
        # See agent_service.py::chat_history_append_func for the duplication prevention this tag results in
        Tag(kind=TagKind.CHAT, name="streamed-to-chat-history"),
    ])

    context.chat_history.append_system_message(
        text=prompt,
        tags=prompt_tags,
    )
    # Intentionally reuse the filtering for the quest CONTENT
    block_indices = filter.filter_chat_history(chat_history_file=context.chat_history.file, filter_for=generation_for)

    task = generator.generate(
        tags=output_tags,
        append_output_to_file=True,
        input_file_id=context.chat_history.file.id,
        output_file_id=context.chat_history.file.id,
        streaming=True,
        input_file_block_index_list=block_indices,
    )
    task.wait()
    blocks = task.output.blocks
    block = blocks[0]
    block = Block.get(block.client, _id=block.id)
    emit(output=block, context=context)
    return block


def await_streamed_block(block: Block, context: AgentContext) -> Block:
    while block.stream_state not in [StreamState.COMPLETE, StreamState.ABORTED]:
        time.sleep(0.4)
        block = Block.get(block.client, _id=block.id)
    context.chat_history.file.refresh()
    return block
