from pydantic import BaseModel, Field
from steamship import PluginInstance, Steamship


class ServerSettings(BaseModel):
    """Server Settings for the AI Adventure Game set by the Game Host.

    These are intended to be set by the game operator (not the user).
    """

    # Image Generation Settings
    default_image_model: str = Field("dall-e", description="")

    # Language Generation Settings
    default_llm_model: str = Field("gpt-3.5-turbo", description="")
    default_llm_temperature: float = Field(0.4, description="")
    default_llm_max_tokens: int = Field(256, description="")

    # Voice Generation Settings
    default_voice_model: str = Field("elevenlabs", description="")

    # User Rank Settings
    max_user_rank: int = Field(
        100, description="The maximum rank that a user can achieve."
    )
    starting_user_rank: int = Field(1, description="The starting rank that a user has.")

    def get_story_generator(self, client: Steamship) -> PluginInstance:
        """Return a plugin instance for the story generator."""
        if self.default_llm_model in ["gpt-3.5-turbo", "gpt-4"]:
            plugin_handle = (
                "gpt-4"  # This is the Steamship plugin, not the actual model.
            )

        return client.use_plugin(
            plugin_handle,
            config={
                "model": self.default_llm_model,
                "max_tokens": self.default_llm_max_tokens,
                "temperature": self.default_llm_temperature,
            },
        )

    def get_image_generator(self, client: Steamship) -> PluginInstance:
        """Return a plugin instance for the image generator."""
        if self.default_image_model in ["dall-e"]:
            plugin_handle = "dall-e"

        return client.use_plugin(plugin_handle)

    def get_voice_generator(self, client: Steamship) -> PluginInstance:
        """Return a plugin instance for the voice generator."""
        if self.default_voice_model in ["elevenlabs"]:
            plugin_handle = "elevenlabs"

        return client.use_plugin(plugin_handle)
