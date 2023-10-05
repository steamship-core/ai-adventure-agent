from pydantic import BaseModel, Field
from steamship import PluginInstance, Steamship, SteamshipError
from steamship.agents.schema.agent import AgentContext

from context_utils import (
    with_background_image_generator,
    with_background_music_generator,
    with_narration_generator,
    with_profile_image_generator,
    with_server_settings,
    with_story_generator,
)


class ServerSettings(BaseModel):
    """Server Settings for the AI Adventure Game set by the Game Host.

    These are intended to be set by the game operator (not the user).
    """

    # Image Generation Settings
    default_profile_image_model: str = Field("dall-e", description="")
    default_background_image_model: str = Field("dall-e", description="")

    # Language Generation Settings
    default_llm_model: str = Field("gpt-3.5-turbo", description="")
    default_llm_temperature: float = Field(0.4, description="")
    default_llm_max_tokens: int = Field(256, description="")

    # Narration Generation Settings
    default_narration_model: str = Field("elevenlabs-test", description="")

    # Narration Generation Settings
    default_background_music_model: str = Field("music-generator", description="")

    def get_story_generator(self, client: Steamship) -> PluginInstance:
        """Return a plugin instance for the story generator."""
        plugin_handle = None

        if self.default_llm_model in ["gpt-3.5-turbo", "gpt-4"]:
            plugin_handle = (
                "gpt-4"  # This is the Steamship plugin, not the actual model.
            )

        if plugin_handle is None:
            raise SteamshipError(message=f"Invalid LLM model: {self.default_llm_model}")

        return client.use_plugin(
            plugin_handle,
            config={
                "model": self.default_llm_model,
                "max_tokens": self.default_llm_max_tokens,
                "temperature": self.default_llm_temperature,
            },
        )

    def get_profile_image_generator(self, client: Steamship) -> PluginInstance:
        """Return a plugin instance for the profile image generator."""
        plugin_handle = None

        if self.default_profile_image_model in ["dall-e"]:
            plugin_handle = "dall-e"

        if plugin_handle is None:
            raise SteamshipError(
                message=f"Invalid Image model: {self.default_profile_image_model}"
            )

        return client.use_plugin(plugin_handle)

    def get_background_image_generator(self, client: Steamship) -> PluginInstance:
        """Return a plugin instance for the background image generator."""
        plugin_handle = None

        if self.default_background_image_model in ["dall-e"]:
            plugin_handle = "dall-e"

        if plugin_handle is None:
            raise SteamshipError(
                message=f"Invalid Image model: {self.default_background_image_model}"
            )

        return client.use_plugin(plugin_handle)

    def get_narration_generator(self, client: Steamship) -> PluginInstance:
        """Return a plugin instance for the narration."""
        plugin_handle = None

        if self.default_narration_model in ["elevenlabs", "elevenlabs-test"]:
            plugin_handle = self.default_narration_model

        if plugin_handle is None:
            raise SteamshipError(
                message=f"Invalid Narration model: {self.default_narration_model}"
            )

        return client.use_plugin(plugin_handle)

    def get_background_music_generator(self, client: Steamship) -> PluginInstance:
        """Return a plugin instance for the background music."""
        plugin_handle = None

        if self.default_background_music_model in ["music-generator"]:
            plugin_handle = self.default_narration_model

        if plugin_handle is None:
            raise SteamshipError(
                message=f"Invalid Background Music model: {self.default_background_music_model}"
            )

        return client.use_plugin(plugin_handle)

    def add_to_agent_context(self, context: AgentContext) -> AgentContext:
        context = with_story_generator(
            self.get_story_generator(context.client), context
        )

        context = with_narration_generator(
            self.get_narration_generator(context.client), context
        )

        context = with_background_music_generator(
            self.get_background_music_generator(context.client), context
        )

        context = with_profile_image_generator(
            self.get_profile_image_generator(context.client), context
        )

        context = with_background_image_generator(
            self.get_background_image_generator(context.client), context
        )

        context = with_server_settings(self, context)

        return context
