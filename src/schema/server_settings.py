from typing import List, Optional

from pydantic import BaseModel, Field
from steamship import PluginInstance, Steamship, SteamshipError
from steamship.agents.llms.openai import ChatOpenAI
from steamship.agents.schema import ChatLLM
from steamship.agents.schema.agent import AgentContext

from schema.game_state import GameState
from utils.context_utils import (
    with_background_image_generator,
    with_background_music_generator,
    with_function_capable_llm,
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

    # Language Generation Settings - Function calling
    default_function_capable_llm_model: str = Field("gpt-4", description="")
    default_function_capable_llm_temperature: float = Field(0.4, description="")
    default_function_capable_llm_max_tokens: int = Field(256, description="")

    # Language Generation Settings - Story telling
    default_story_model: str = Field("gpt-4", description="")
    default_story_temperature: float = Field(0.4, description="")
    default_story_max_tokens: int = Field(256, description="")

    # Narration Generation Settings
    default_narration_model: str = Field("elevenlabs", description="")

    # Narration Generation Settings
    default_background_music_model: str = Field("music-generator", description="")

    def _select_model(
        self,
        allowed: List[str],
        default: Optional[str] = None,
        preferred: Optional[str] = None,
    ) -> str:
        if preferred and preferred in allowed:
            return preferred
        if default in allowed:
            return default
        raise SteamshipError(
            message=f"Invalid model selection (preferred={preferred}, default={default}). Only the following are allowed: {allowed}"
        )

    def get_story_generator(
        self, client: Steamship, preferred_model: Optional[str] = None
    ) -> PluginInstance:
        """Return a plugin instance for the story generator."""

        open_ai_models = ["gpt-3.5-turbo", "gpt-4"]
        replicate_models = ["dolly_v2", "llama_v2"]

        model_name = self._select_model(
            open_ai_models + replicate_models,
            default=self.default_story_model,
            preferred=preferred_model,
        )

        plugin_handle = None
        if model_name in open_ai_models:
            plugin_handle = "gpt-4"
        elif model_name in replicate_models:
            plugin_handle = "replicate-llm"

        return client.use_plugin(
            plugin_handle,
            config={
                "model": model_name,
                "max_tokens": self.default_story_max_tokens,
                "temperature": self.default_story_temperature,
            },
        )

    def get_function_capable_llm(self, client: Steamship) -> ChatLLM:
        """Return a plugin instance for the story generator."""
        return ChatOpenAI(client)

    def get_profile_image_generator(
        self, client: Steamship, preferred_model: Optional[str] = None
    ) -> PluginInstance:
        """Return a plugin instance for the profile image generator."""
        plugin_handle = self._select_model(
            ["dall-e"],
            default=self.default_profile_image_model,
            preferred=preferred_model,
        )
        return client.use_plugin(plugin_handle)

    def get_background_image_generator(
        self, client: Steamship, preferred_model: Optional[str] = None
    ) -> PluginInstance:
        """Return a plugin instance for the background image generator."""
        plugin_handle = self._select_model(
            ["dall-e"],
            default=self.default_background_image_model,
            preferred=preferred_model,
        )
        return client.use_plugin(plugin_handle)

    def get_narration_generator(
        self, client: Steamship, preferred_model: Optional[str] = None
    ) -> PluginInstance:
        """Return a plugin instance for the narration."""
        plugin_handle = self._select_model(
            ["elevenlabs"],
            default=self.default_narration_model,
            preferred=preferred_model,
        )
        return client.use_plugin(plugin_handle)

    def get_background_music_generator(
        self, client: Steamship, preferred_model: Optional[str] = None
    ) -> PluginInstance:
        """Return a plugin instance for the background music."""
        plugin_handle = self._select_model(
            ["music-generator"],
            default=self.default_narration_model,
            preferred=preferred_model,
        )
        return client.use_plugin(plugin_handle)

    def add_to_agent_context(
        self, context: AgentContext, game_state: GameState
    ) -> AgentContext:
        # TODO: This feels like a great way to interact with AgentContext, but this is a LOT of loading that has to
        # happen on EVERY call. Perhaps we move this to happen on-demand to speed things up if latency is bad.

        context = with_story_generator(
            self.get_story_generator(
                context.client, game_state.preferences.story_model
            ),
            context,
        )

        context = with_narration_generator(
            self.get_narration_generator(
                context.client, game_state.preferences.narration_model
            ),
            context,
        )

        context = with_background_music_generator(
            self.get_background_music_generator(
                context.client, game_state.preferences.background_music_model
            ),
            context,
        )

        context = with_profile_image_generator(
            self.get_profile_image_generator(
                context.client, game_state.preferences.profile_image_model
            ),
            context,
        )

        context = with_background_image_generator(
            self.get_background_image_generator(
                context.client, game_state.preferences.background_image_model
            ),
            context,
        )

        # User can't pick function-calling model. That's too error-prone.
        context = with_function_capable_llm(
            self.get_function_capable_llm(context.client), context
        )

        context = with_server_settings(self, context)

        return context
