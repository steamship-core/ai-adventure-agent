"""These are a set of utilities for interacting with the AgentContext object.

The following things should ALWAYS be done via these functions:
- getting / setting of game state
- getting or generators
- manipulations on active chat histories

That way these can as global accessors into the shared AgentContext object that is passed around, with persistence
layered on top to boot.

That reduces the need of the game code to perform verbose plumbing operations.
"""
import logging
from typing import List, Optional, Union

from steamship import Block, PluginInstance, Tag
from steamship.agents.logging import AgentLogging
from steamship.agents.schema import ChatHistory, ChatLLM
from steamship.agents.schema.agent import AgentContext
from steamship.data import TagValueKey
from steamship.utils.kv_store import KeyValueStore

_STORY_GENERATOR_KEY = "story-generator"
_FUNCTION_CAPABLE_LLM = (
    "function-capable-llm"  # This could be distinct from the one generating the story.
)
_BACKGROUND_MUSIC_GENERATOR_KEY = "background-music-generator"
_BACKGROUND_IMAGE_GENERATOR_KEY = "background-image-generator"
_PROFILE_IMAGE_GENERATOR_KEY = "profile-image-generator"
_NARRATION_GENERATOR_KEY = "narration-generator"
_SERVER_SETTINGS_KEY = "server-settings"
_game_state_KEY = "user-settings"


def with_story_generator(
    instance: PluginInstance, context: AgentContext
) -> AgentContext:
    context.metadata[_STORY_GENERATOR_KEY] = instance
    return context


def with_function_capable_llm(instance: ChatLLM, context: AgentContext) -> AgentContext:
    context.metadata[_FUNCTION_CAPABLE_LLM] = instance
    return context


def with_background_music_generator(
    instance: PluginInstance, context: AgentContext
) -> AgentContext:
    context.metadata[_BACKGROUND_MUSIC_GENERATOR_KEY] = instance
    return context


def with_background_image_generator(
    instance: PluginInstance, context: AgentContext
) -> AgentContext:
    context.metadata[_BACKGROUND_IMAGE_GENERATOR_KEY] = instance
    return context


def with_profile_image_generator(
    instance: PluginInstance, context: AgentContext
) -> AgentContext:
    context.metadata[_PROFILE_IMAGE_GENERATOR_KEY] = instance
    return context


def with_narration_generator(
    instance: PluginInstance, context: AgentContext
) -> AgentContext:
    context.metadata[_NARRATION_GENERATOR_KEY] = instance
    return context


def with_server_settings(
    server_settings: "ServerSettings", context: AgentContext  # noqa: F821
) -> "ServerSettings":  # noqa: F821
    context.metadata[_SERVER_SETTINGS_KEY] = server_settings
    return context


def with_game_state(
    server_settings: "GameState", context: AgentContext  # noqa: F821
) -> "GameState":  # noqa: F821
    context.metadata[_game_state_KEY] = server_settings
    return context


def get_story_text_generator(
    context: AgentContext, default: Optional[PluginInstance] = None
) -> Optional[PluginInstance]:
    return context.metadata.get(_STORY_GENERATOR_KEY, default)


def get_background_music_generator(
    context: AgentContext, default: Optional[PluginInstance] = None
) -> Optional[PluginInstance]:
    return context.metadata.get(_BACKGROUND_MUSIC_GENERATOR_KEY, default)


def get_background_image_generator(
    context: AgentContext, default: Optional[PluginInstance] = None
) -> Optional[PluginInstance]:
    return context.metadata.get(_BACKGROUND_IMAGE_GENERATOR_KEY, default)


def get_profile_image_generator(
    context: AgentContext, default: Optional[PluginInstance] = None
) -> Optional[PluginInstance]:
    return context.metadata.get(_PROFILE_IMAGE_GENERATOR_KEY, default)


def get_audio_narration_generator(
    context: AgentContext, default: Optional[PluginInstance] = None
) -> Optional[PluginInstance]:
    return context.metadata.get(_NARRATION_GENERATOR_KEY, default)


def get_server_settings(
    context: AgentContext, default: Optional["ServerSettings"] = None  # noqa: F821
) -> Optional["ServerSettings"]:  # noqa: F821
    return context.metadata.get(_SERVER_SETTINGS_KEY, default)


def get_game_state(
    context: AgentContext, default: Optional["GameState"] = None  # noqa: F821
) -> Optional["GameState"]:  # noqa: F821
    return context.metadata.get(_game_state_KEY, default)


def save_game_state(game_state, context: AgentContext):
    """Save GameState to the KeyValue store."""

    # Save it to the KV Store
    key = "GameState"
    value = game_state.dict()
    kv = KeyValueStore(context.client, key)
    kv.set(key, value)

    # Also save it to the context
    context.metadata[_game_state_KEY] = game_state


def get_current_quest(context: AgentContext) -> Optional["Quest"]:  # noqa: F821
    """Return current Quest, or None."""

    game_state = get_game_state(context)

    if not game_state:
        return None

    if not game_state.current_quest:
        return None

    for quest in game_state.quests or []:
        if quest.name == game_state.current_quest:
            return quest

    return None


def get_current_conversant(
    context: AgentContext,
) -> Optional["NpcCharacter"]:  # noqa: F821
    """Return the NpcCharacter of the current conversation, or None."""
    game_state = get_game_state(context)

    if not game_state:
        return None

    if not game_state.in_conversation_with:
        return None

    if not game_state.camp:
        return None

    if not game_state.camp.npcs:
        return None

    for npc in game_state.camp.npcs or []:
        if npc.name == game_state.in_conversation_with:
            return npc

    return None


def switch_history_to_current_conversant(
    context: AgentContext,
) -> AgentContext:  # noqa: F821
    """Return the NpcCharacter of the current conversation, or None."""
    npc = get_current_conversant(context)

    if npc:
        logging.info(
            f"Switching to NPC Chat History: {npc.name}.",
            extra={
                AgentLogging.IS_MESSAGE: True,
                AgentLogging.MESSAGE_TYPE: AgentLogging.THOUGHT,
                AgentLogging.MESSAGE_AUTHOR: AgentLogging.AGENT,
            },
        )
        history = ChatHistory.get_or_create(
            context.client, {"id": npc.name}, [], searchable=True
        )
        context.chat_history = history
    return context


def switch_history_to_current_quest(
    context: AgentContext,
) -> AgentContext:  # noqa: F821
    """Return the NpcCharacter of the current conversation, or None."""
    quest = get_current_quest(context)

    if quest:
        logging.info(
            f"Switching to Quest Chat History: {quest.name}.",
            extra={
                AgentLogging.IS_MESSAGE: True,
                AgentLogging.MESSAGE_TYPE: AgentLogging.THOUGHT,
                AgentLogging.MESSAGE_AUTHOR: AgentLogging.AGENT,
            },
        )
        history = ChatHistory.get_or_create(
            context.client, {"id": f"quest:{quest.name}"}, [], searchable=True
        )
        context.chat_history = history
    return context


def get_function_capable_llm(
    context: AgentContext, default: Optional[ChatLLM] = None  # noqa: F821
) -> Optional[ChatLLM]:  # noqa: F821
    return context.metadata.get(_FUNCTION_CAPABLE_LLM, default)


def _key_for_question(blocks: List[Block], key: Optional[str] = None) -> str:
    """The lookup key for a particular question being asked of the user.

    This can be used to tell -- in the "future" -- if the value being awaited is the same as the value last solicited.
    """
    if key:
        return key

    ret = ""
    for block in blocks:
        if block.text:
            ret += block.text
        else:
            ret += block.url
    return ret


def ask_user(
    question: Union[str, List[Block]], context: AgentContext, key: Optional[str] = None
):
    """Asks the user a question. Can be used like `input` in Python.

    USAGE:

        name = ask_user("What is your name?")

    RESULT:

        If the key exists in the game_state object.



    """
    BASE_TAGS = [
        Tag(
            kind="request-id",
            name=context.request_id,
            value={TagValueKey.STRING_VALUE.value: context.request_id},
        )
    ]

    # Make sure question is List[Block]
    if isinstance(question, str):
        question = [Block(text=question, tags=BASE_TAGS)]
