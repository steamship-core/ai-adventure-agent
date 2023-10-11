from pydantic import BaseModel, Field


class Preferences(BaseModel):
    """Information about a quest."""

    class Config:
        arbitrary_types_allowed = True

    profile_image_model: str = Field(
        "dall-e", description="Model used for profile image generation"
    )
    background_image_model: str = Field(
        "dall-e", description="Model used for background image generation"
    )
    story_model: str = Field(
        "gpt-4", description="Model used for story generation (not function calling)"
    )
    narration_model: str = Field(
        "elevenlabs", description="Model used for audio narration"
    )
    background_music_model: str = Field(
        "music-generator", description="Model used for background music generation"
    )

    def update_from_web(self, other: "Preferences"):
        """Performs a gentle update so that the website doesn't accidentally blast over this if it diverges in structure."""
        if other.profile_image_model:
            self.profile_image_model = other.profile_image_model
        if other.background_image_model:
            self.background_image_model = other.background_image_model
        if other.story_model:
            self.story_model = other.story_model
        if other.narration_model:
            self.narration_model = other.narration_model
        if other.background_music_model:
            self.background_music_model = other.background_music_model
