from typing import List, Optional

from pydantic import BaseModel, Field
from steamship import SteamshipError


class ServerSettings(BaseModel):
    """Server Settings for the AI Adventure Game set by the Game Host.

    These are intended to be set by the game operator (not the user).
    """

    # Image Generation Settings
    # default_image_generator: str = Field("StableDiffusionWithLorasImageGenerator", description="")  # TODO(doug): fix

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
    # default_background_music_model: str = Field("music-generator", description="")  # TODO(doug): fix

    # Energy Management
    quest_cost: int = Field(10, description="The cost of going on one quest")

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
