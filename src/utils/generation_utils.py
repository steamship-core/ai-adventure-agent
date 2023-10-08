"""
Like context_utils, this is meant to provide a light-weight set of utilities.

The goal is to enable the game designer work in a high signal-to-noise environment, like this:

    send_background_music("description", context)
    send_assistant_message("Hi there!", context)

While at the same time not committing to any huge abstraction overhead: this is just a light-weight set of helper
functions whose mechanics can change under the hood as we discover better ways to do things, and the game developer
doesn't need to know.
"""
from typing import Optional

from steamship import Block
from steamship.agents.schema import AgentContext

from utils.context_utils import (
    append_to_chat_history_and_emit,
    get_audio_narration_generator,
    get_background_image_generator,
    get_background_music_generator,
    get_story_text_generator,
)


def send_background_music(prompt: str, context: AgentContext) -> Optional[Block]:
    """Generates and sends background music to the player."""
    generator = get_background_music_generator(context)
    task = generator.generate(
        text=prompt,
        make_output_public=True,
        streaming=True,
    )

    # TODO: Figure out how to do this in a way that's treaming friendly AND sync friendly
    task.wait()
    block = task.output.blocks[0]
    append_to_chat_history_and_emit(context, block=block)
    return block


def send_background_image(prompt: str, context: AgentContext) -> Optional[Block]:
    """Generates and sends a background image to the player."""
    generator = get_background_image_generator(context)
    task = generator.generate(
        text=prompt,
        make_output_public=True,
        streaming=True,
    )

    # TODO: Figure out how to do this in a way that's treaming friendly AND sync friendly
    task.wait()
    block = task.output.blocks[0]
    append_to_chat_history_and_emit(context, block=block)
    return block


def send_audio_narration(block: Block, context: AgentContext) -> Optional[Block]:
    """Generates and sends a background image to the player."""
    generator = get_audio_narration_generator(context)
    task = generator.generate(
        text=block.text,
        make_output_public=True,
        streaming=True,
    )

    # TODO: Figure out how to do this in a way that's treaming friendly AND sync friendly
    task.wait()
    block = task.output.blocks[0]
    append_to_chat_history_and_emit(context, block=block)
    return block


def send_story_generation(prompt: str, context: AgentContext) -> Optional[Block]:
    """Generates and sends a background image to the player."""

    generator = get_story_text_generator(context)
    context.chat_history.append_system_message(prompt)
    task = generator.generate(context.chat_history.file.id, streaming=True)

    # TODO: Figure out how to do this in a way that's streaming friendly AND sync friendly
    # TODO: Figure out how to stream narration in a way that's streaming friendly AND sync friendly
    task.wait()
    block = task.output.blocks[0]
    append_to_chat_history_and_emit(context, block=block)
    return block
