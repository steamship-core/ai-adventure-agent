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
from typing import Optional

from steamship import PluginInstance
from steamship.agents.logging import AgentLogging
from steamship.agents.schema import ChatHistory, ChatLLM
from steamship.agents.schema.agent import AgentContext
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
_USER_SETTINGS_KEY = "user-settings"


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


def with_user_settings(
    server_settings: "UserSettings", context: AgentContext  # noqa: F821
) -> "UserSettings":  # noqa: F821
    context.metadata[_USER_SETTINGS_KEY] = server_settings
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


def get_user_settings(
    context: AgentContext, default: Optional["UserSettings"] = None  # noqa: F821
) -> Optional["UserSettings"]:  # noqa: F821
    return context.metadata.get(_USER_SETTINGS_KEY, default)


def save_user_settings(user_settings, context: AgentContext):
    """Save UserSettings to the KeyValue store."""

    # Save it to the KV Store
    key = "UserSettings"
    value = user_settings.dict()
    kv = KeyValueStore(context.client, key)
    kv.set(key, value)

    # Also save it to the context
    context.metadata[_USER_SETTINGS_KEY] = user_settings


def get_current_quest(context: AgentContext) -> Optional["Quest"]:  # noqa: F821
    """Return current Quest, or None."""

    user_settings = get_user_settings(context)

    if not user_settings:
        return None

    if not user_settings.current_quest:
        return None

    for quest in user_settings.quests or []:
        if quest.name == user_settings.current_quest:
            return quest

    return None


def get_current_conversant(
    context: AgentContext,
) -> Optional["NpcCharacter"]:  # noqa: F821
    """Return the NpcCharacter of the current conversation, or None."""
    user_settings = get_user_settings(context)

    if not user_settings:
        return None

    if not user_settings.in_conversation_with:
        return None

    if not user_settings.camp:
        return None

    if not user_settings.camp.npcs:
        return None

    for npc in user_settings.camp.npcs or []:
        if npc.name == user_settings.in_conversation_with:
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
