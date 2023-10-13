import sys
from random import randint

from pydantic import BaseModel, Field


class Preferences(BaseModel):
    """Information about a quest."""

    class Config:
        arbitrary_types_allowed = True

    seed: int = Field(
        default=randint(0, sys.maxsize),  # noqa: S311
        description="Used to pin a consistent style for game for music and image generation.",
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
        """Performs a gentle update so that the website doesn't accidentally blast over this if it diverges in
        structure."""
        if other.story_model:
            self.story_model = other.story_model
        if other.narration_model:
            self.narration_model = other.narration_model
