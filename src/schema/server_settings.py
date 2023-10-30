from typing import List, Optional

from pydantic import BaseModel, Field
from steamship import SteamshipError

_SUPPORTED_ELEVEN_VOICES = {
    "knightly": {
        "id": "qk9eXb51CntEhbbRU1ny",
        "label": "Knightly",
        "description": "Old male british man. A deep and smooth voice for storytelling and podcast.",
    },
    "oswald": {
        "id": "Gc2LOaLVvOzXc6nU30Eg",
        "label": "Oswald",
        "description": "Intelligent Professor.",
    },
    "marcus": {
        "id": "IdZRgDjRZjFkdCn6m1Nl",
        "label": "Marcus",
        "description": "An authoritative and deep voice. Great for audio books or news.",
    },
    "bria": {
        "id": "Y4j1j6KUWh4GF02bCvVL",
        "label": "Bria",
        "description": "A young female with a softly spoken tone, perfect for storytelling or ASMR.",
    },
    "alex": {
        "id": "7Y4ogNdqWsNlFymJ9lZw",
        "label": "Alex",
        "description": "Young american man. Is a strong and expressive narrator.",
    },
    "valentino": {
        "id": "15zz9lmuNt401tH3HZ8E",
        "label": "Valentino",
        "description": "A great voice with depth. The voice is deep with a great accent, and works well for meditations.",
    },
    "natasha": {
        "id": "YmNvmviYqx1g64e2stQC",
        "label": "Natasha",
        "description": "A valley girl female voice. Great for shorts.",
    },
    "brian": {
        "id": "EKwMQkKDRzyT7h19ccvV",
        "label": "Brian",
        "description": "Great voice for nature documentaries.",
    },
    "joanne": {
        "id": "p7toRxCsJYlANtoQG286",
        "label": "Joanne",
        "description": "Young american woman. A soft and pleasant voice for a great character.",
    },
}


class ServerSettings(BaseModel):
    """Server Settings for the AI Adventure Game set by the Game Host.

    These are intended to be set by the game operator (not the user).
    """

    # Image Generation Settings
    default_image_generation_lora: str = Field(
        default="https://civitai.com/api/download/models/123593",
        description="LoRA to use for image generation. This MUST be a known SDXL-based LoRA.",
    )

    # Language Generation Settings - Function calling
    default_function_capable_llm_model: str = Field("gpt-3.5-turbo", description="")
    default_function_capable_llm_temperature: float = Field(0.4, description="")
    default_function_capable_llm_max_tokens: int = Field(512, description="")

    # Language Generation Settings - Story telling
    default_story_model: str = Field("gpt-3.5-turbo", description="")
    default_story_temperature: float = Field(0.4, description="")
    default_story_max_tokens: int = Field(512, description="")

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
