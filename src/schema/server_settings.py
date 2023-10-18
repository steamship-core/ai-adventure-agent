from typing import List, Optional

from pydantic import BaseModel, Field
from steamship import SteamshipError


def validate_prompt_args(prompt: str, valid_args: List[str]):
    return True


class ServerSettings(BaseModel):
    """Server Settings for the AI Adventure Game set by the Game Host.

    These are intended to be set by the game operator (not the user).
    """

    # Image Generation Settings
    # default_image_generator: str = Field("StableDiffusionWithLorasImageGenerator", description="")  # TODO(doug): fix

    # Language Generation Settings - Function calling
    default_function_capable_llm_model: str = Field("gpt-3.5-turbo", description="")
    default_function_capable_llm_temperature: float = Field(0.4, description="")
    default_function_capable_llm_max_tokens: int = Field(512, description="")

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

    # Prompts

    camp_image_prompt: str = Field(
        "(pixel art) {tone} {genre} camp.",
        description="Prompt for generating camp images.",
    )
    item_image_prompt: str = Field(
        "(pixel art) 16-bit retro-game sprite for an item in a hero's inventory. The items's name is: {name}. The item's description is: {description}.",
        description="Prompt for generating item images.",
    )
    profile_image_prompt: str = Field(
        "(pixel art) 16-bit retro-game style profile picture of a hero on an adventure. The hero's name is: {name}. The hero has the following background: {background}. The hero has a description of: {description}.",
        description="Prompt for generating profile images.",
    )

    quest_background_image_prompt: str = Field(
        "(pixel art) background scene for a quest. The scene being depicted is: {description}",
        description="Prompt for generating quest background images.",
    )

    music_prompt: str = Field(
        "16-bit game score for a quest game scene. {genre} genre. {tone}. Scene description: {description}",
        description="Prompt for generating music.",
    )

    # Loras

    camp_image_loras: List[str] = Field(
        ["https://civitai.com/api/download/models/135931"],
        description="Loras for generating camp images.",
    )

    item_image_loras: List[str] = Field(
        ["https://civitai.com/api/download/models/135931"],
        description="Loras for generating item images.",
    )

    profile_image_loras: List[str] = Field(
        ["https://civitai.com/api/download/models/135931"],
        description="Lorase for generating profile images.",
    )

    quest_background_image_loras: List[str] = Field(
        ["https://civitai.com/api/download/models/135931"],
        description="Loras for generating quest background images.",
    )

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

    def update_from_web(self, other: "ServerSettings"):  # noqa: C901
        """Perform a gentle update so that the website doesn't accidentally blast over this if it diverges in
        structure."""

        if other.default_function_capable_llm_model:
            self.default_function_capable_llm_model = (
                other.default_function_capable_llm_model
            )

        if other.default_function_capable_llm_temperature:
            self.default_function_capable_llm_temperature = (
                other.default_function_capable_llm_temperature
            )

        if other.default_function_capable_llm_max_tokens:
            self.default_function_capable_llm_max_tokens = (
                other.default_function_capable_llm_max_tokens
            )

        if other.default_story_model:
            self.default_story_model = other.default_story_model

        if other.default_story_temperature:
            self.default_story_temperature = other.default_story_temperature

        if other.default_story_max_tokens:
            self.default_story_max_tokens = other.default_story_max_tokens

        if other.default_narration_model:
            self.default_narration_model = other.default_narration_model

        if other.quest_cost:
            self.quest_cost = other.quest_cost

        # TODO: Validate that they don't have bad interpolated variables below.

        if other.camp_image_prompt:
            validate_prompt_args(other.camp_image_prompt, ["tone", "genre"])
            self.camp_image_prompt = other.camp_image_prompt
            self.camp_image_loras = other.camp_image_loras

        if other.item_image_prompt:
            validate_prompt_args(other.item_image_prompt, ["name", "description"])
            self.item_image_prompt = other.item_image_prompt
            self.item_image_loras = other.item_image_loras

        if other.profile_image_prompt:
            validate_prompt_args(
                other.profile_image_prompt,
                ["name", "background", "description", "tone", "genre"],
            )
            self.profile_image_prompt = other.profile_image_prompt
            self.profile_image_loras = other.profile_image_loras

        if other.quest_background_image_prompt:
            validate_prompt_args(other.quest_background_image_prompt, ["description"])
            self.quest_background_image_prompt = other.quest_background_image_prompt
            self.quest_background_image_loras = other.quest_background_image_loras

        if other.music_prompt:
            validate_prompt_args(other.music_prompt, ["genre", "tone", "description"])
            self.music_prompt = other.music_prompt
