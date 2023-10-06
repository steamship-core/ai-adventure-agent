from typing import Optional

from steamship import PluginInstance
from steamship.agents.schema import ChatLLM
from steamship.agents.schema.agent import AgentContext

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


def get_story_generator(
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


def get_narration_generator(
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


def get_current_quest(context: AgentContext) -> Optional["Quest"]:  # noqa: F821
    user_settings = get_user_settings(context)

    if not user_settings:
        return None

    if not user_settings.current_quest:
        return None

    for quest in user_settings.quests or []:
        if quest.name == user_settings.current_quest:
            return quest


def get_function_capable_llm(
    context: AgentContext, default: Optional[ChatLLM] = None  # noqa: F821
) -> Optional[ChatLLM]:  # noqa: F821
    return context.metadata.get(_FUNCTION_CAPABLE_LLM, default)
