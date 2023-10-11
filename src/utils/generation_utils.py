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
from typing import Optional

from steamship import Block, Tag
from steamship.agents.schema import AgentContext
from steamship.data import TagKind
from steamship.data.tags.tag_constants import ChatTag, RoleTag, TagValueKey

from utils.context_utils import (
    emit,
    get_audio_narration_generator,
    get_background_image_generator,
    get_background_music_generator,
    get_story_text_generator,
)
from utils.tags import AgentStatusMessageTag


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


def send_story_generation(prompt: str, context: AgentContext) -> Optional[Block]:
    """Generates and sends a background image to the player."""

    generator = get_story_text_generator(context)
    # context.chat_history.append_system_message(prompt)

    logging.warning("THIS ISN'T GOING TO USE THE WHOLE CHAT HISTORY!")

    tags = [
        Tag(
            kind=TagKind.CHAT,
            name=ChatTag.ROLE,
            value={TagValueKey.STRING_VALUE: RoleTag.ASSISTANT},
        ),
        Tag(kind=TagKind.CHAT, name=ChatTag.MESSAGE),
        # See agent_service.py::chat_history_append_func for the duplication prevention this tag results in
        Tag(kind=TagKind.CHAT, name="streamed-to-chat-history"),
    ]

    logging.warning(f"Generating: {prompt}")
    task = generator.generate(
        text=prompt,
        tags=tags,
        append_output_to_file=True,
        output_file_id=context.chat_history.file.id,
        streaming=True,
    )
    task.wait()
    blocks = task.output.blocks
    block = blocks[0]
    emit(output=block, context=context)
    return block
