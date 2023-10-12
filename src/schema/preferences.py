import json
import sys
from random import randint
from typing import Any, Dict

from pydantic import BaseModel, Field


class Preferences(BaseModel):
    """Information about a quest."""

    class Config:
        arbitrary_types_allowed = True

    seed: int = Field(
        default=randint(0, sys.maxsize),  # noqa: S311
        description="Used to pin a consistent style for game for music and image generation.",
    )

    profile_image_model: str = Field(
        "fal-sd-lora-image-generator",
        description="Model used for profile image generation",
    )

    background_image_model: str = Field(
        "fal-sd-lora-image-generator",
        description="Model used for background image generation",
    )

    item_image_model: str = Field(
        "fal-sd-lora-image-generator",
        description="Model used for item image generation",
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

    def background_image_config(self) -> Dict[str, Any]:
        return {
            "seed": self.seed,
            "image_size": "landscape_16_9",
            "loras": json.dumps(
                [{"path": "https://civitai.com/api/download/models/135931"}]
            ),
        }

    def profile_image_config(self) -> Dict[str, Any]:
        return {
            "seed": self.seed,
            "image_size": "portrait_4_3",
            "loras": json.dumps(
                [{"path": "https://civitai.com/api/download/models/135931"}]
            ),
        }

    def item_image_config(self) -> Dict[str, Any]:
        # TODO(doug): refactor for matching based on model name, or similar
        return {
            "seed": self.seed,
            "image_size": "square",
            "loras": json.dumps(
                [{"path": "https://civitai.com/api/download/models/135931"}]
            ),
        }
