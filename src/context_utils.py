from typing import Optional

from steamship import PluginInstance
from steamship.agents.schema.agent import AgentContext

_STORY_GENERATOR_KEY = "story-generator"
_BACKGROUND_MUSIC_GENERATOR_KEY = "background-music-generator"
_BACKGROUND_IMAGE_GENERATOR_KEY = "background-image-generator"
_PROFILE_IMAGE_GENERATOR_KEY = "profile-image-generator"
_NARRATION_GENERATOR_KEY = "narration-generator"
_SERVER_SETTINGS_KEY = "server-settings"


def with_story_generator(
    instance: PluginInstance, context: AgentContext
) -> AgentContext:
    context.metadata[_STORY_GENERATOR_KEY] = instance
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
