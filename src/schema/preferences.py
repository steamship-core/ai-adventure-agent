from random import randint

from pydantic import BaseModel, Field


class Preferences(BaseModel):
    """Information about a quest."""

    class Config:
        arbitrary_types_allowed = True

    seed: int = Field(
        default=randint(0, 2147483647),  # noqa: S311
        description="Used to pin a consistent style for game for music and image generation.",
    )

    story_model: str = Field(
        "gpt-3.5-turbo",
        description="Model used for story generation (not function calling)",
    )
    narration_model: str = Field(
        "elevenlabs", description="Model used for audio narration"
    )
    image_generation_lora: str = Field(
        default="https://civitai.com/api/download/models/123593",
        description="Preferred LoRA to use for image generation. This MUST be a known SDXL-based LoRA."
        "Known models: [https://civitai.com/api/download/models/135931, "
        "https://civitai.com/api/download/models/123593]",
    )

    def update_from_web(self, other: "Preferences"):
        """Performs a gentle update so that the website doesn't accidentally blast over this if it diverges in
        structure."""
        if other.story_model:
            self.story_model = other.story_model
        if other.narration_model:
            self.narration_model = other.narration_model
        if other.image_generation_lora:
            self.image_generation_lora = other.image_generation_lora
