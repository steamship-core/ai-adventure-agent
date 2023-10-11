"""
Like context_utils, this is meant to provide a light-weight set of utilities.

The goal is to enable the game designer work in a high signal-to-noise environment, like this:

    send_background_music("description", context)
    send_assistant_message("Hi there!", context)

While at the same time not committing to any huge abstraction overhead: this is just a light-weight set of helper
functions whose mechanics can change under the hood as we discover better ways to do things, and the game developer
doesn't need to know.
"""
import logging
import time
from typing import Optional

from steamship import Block, Tag, File
from steamship.agents.schema import AgentContext
from steamship.data import TagKind
from steamship.data.block import StreamState
from steamship.data.tags.tag_constants import ChatTag, RoleTag, TagValueKey

from utils.context_utils import (
    emit,
    get_audio_narration_generator,
    get_background_image_generator,
    get_background_music_generator,
    get_story_text_generator,
)
from utils.tags import TagKindExtensions, CharacterTag, StoryContextTag, QuestTag


def send_background_music(prompt: str, context: AgentContext) -> Optional[Block]:
    """Generates and sends background music to the player."""
    generator = get_background_music_generator(context)
    task = generator.generate(
        text=prompt,
        make_output_public=True,
        # streaming=True,
    )

    # TODO: Figure out how to do this in a way that's treaming friendly AND sync friendly
    task.wait()
    block = task.output.blocks[0]
    emit(output=block, context=context)
    return block


def send_background_image(prompt: str, context: AgentContext) -> Optional[Block]:
    """Generates and sends a background image to the player."""
    generator = get_background_image_generator(context)
    task = generator.generate(
        text=prompt,
        make_output_public=True,
        # streaming=True,
    )

    # TODO: Figure out how to do this in a way that's treaming friendly AND sync friendly
    task.wait()
    block = task.output.blocks[0]
    emit(output=block, context=context)
    return block


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


def send_story_generation(prompt: str, context: AgentContext) -> Optional[Block]:
    """Generates and sends a background image to the player."""

    generator = get_story_text_generator(context)
    # context.chat_history.append_system_message(prompt)

    tags = [
        Tag(
            kind=TagKind.CHAT,
            name=ChatTag.ROLE,
            value={TagValueKey.STRING_VALUE: RoleTag.ASSISTANT},
        ),
        Tag(kind=TagKind.CHAT, name=ChatTag.MESSAGE),
        # See agent_service.py::chat_history_append_func for the duplication prevention this tag results in
        Tag(kind=TagKind.CHAT, name="streamed-to-chat-history"),
        Tag(kind=TagKindExtensions.QUEST, name=QuestTag.QUEST_CONTENT)
    ]

    context.chat_history.append_system_message(text=prompt,
                                               tags=[Tag(kind=TagKindExtensions.QUEST, name=QuestTag.QUEST_PROMPT)])
    block_indices = filter_block_indices(context.chat_history.file)
    # logging.warning(f"Generating: {prompt}")

    task = generator.generate(
        # text=prompt, # Don't want to pass this if we're passing blocks
        tags=tags,
        append_output_to_file=True,
        input_file_id=context.chat_history.file.id,
        output_file_id=context.chat_history.file.id,
        streaming=True,
        input_file_block_index_list=block_indices,
    )
    task.wait()
    blocks = task.output.blocks
    block = blocks[0]
    emit(output=block, context=context)
    return block


def filter_block_indices(chat_history_file: File) -> [int]:

    allowed_kind_names = [
        (TagKindExtensions.CHARACTER, CharacterTag.NAME),
        (TagKindExtensions.CHARACTER, CharacterTag.MOTIVATION),
        (TagKindExtensions.CHARACTER, CharacterTag.DESCRIPTION),
        (TagKindExtensions.CHARACTER, CharacterTag.BACKGROUND),
        (TagKindExtensions.CHARACTER, CharacterTag.INVENTORY),
        (TagKindExtensions.STORY_CONTEXT, StoryContextTag.GENRE),
        (TagKindExtensions.STORY_CONTEXT, StoryContextTag.TONE),
        (TagKindExtensions.QUEST, QuestTag.QUEST_CONTENT),
        (TagKindExtensions.QUEST, QuestTag.USER_SOLUTION),
        (TagKindExtensions.QUEST, QuestTag.QUEST_PROMPT)

    ]

    result = []
    print("Generation input ************")
    for block in chat_history_file.blocks:
        will_include = False
        matching_tag = None
        for tag in block.tags:
            for (kind, name) in allowed_kind_names:
                if tag.kind == kind and tag.name == name:
                    will_include = True
                    matching_tag = tag
        if will_include:
            result.append(block.index_in_file)
            print(f"{block.index_in_file} [{matching_tag.kind} {matching_tag.name}] {block.text}")

    print("******************")
    return result


def await_streamed_block(block: Block):
    while block.stream_state == StreamState.STARTED:
        time.sleep(1)
        block = Block.get(block.client, _id=block.id)