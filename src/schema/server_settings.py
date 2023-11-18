import re
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field
from steamship import SteamshipError

from schema.quest import QuestDescription
from schema.stable_diffusion_theme import StableDiffusionTheme


def validate_prompt_args(
    prompt: str, valid_args: List[str], prompt_name: str
) -> Optional[str]:
    regex = r"\{(.*?)\}"
    matches = re.finditer(regex, prompt)
    variable_names = sorted({match.group(1) for match in matches})
    missing_vars = []
    for variable_name in variable_names:
        if variable_name not in valid_args:
            missing_vars.append(variable_name)

    if len(missing_vars) > 0:
        return f"{prompt_name} uses the following variable names which are not available: [{' '.join(missing_vars)}]. The prompt was: {prompt}"
    else:
        return None


class AvailableVoice(str, Enum):
    DOROTHY = "dorothy"
    KNIGHTLY = "knightly"
    OSWALD = "oswald"
    MARCUS = "marcus"
    BRIA = "bria"
    ALEX = "alex"
    VALENTINO = "valentino"
    NATASHA = "natasha"
    BRIAN = "brian"
    JOANNE = "joanne"


_SUPPORTED_ELEVEN_VOICES = {
    "dorothy": {
        "id": "ThT5KcBeYPX3keUQqHPh",
        "label": "Dorothy",
        "description": "A young female british voice, good for children's stories.",
    },
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

    # Language Generation Settings - Function calling
    default_function_capable_llm_model: str = Field("gpt-3.5-turbo", description="")
    default_function_capable_llm_temperature: float = Field(0.0, description="")
    default_function_capable_llm_max_tokens: int = Field(512, description="")

    # Language Generation Settings - Story telling
    default_story_model: str = Field("gpt-3.5-turbo", description="")
    default_story_temperature: float = Field(0.7, description="")
    default_story_max_tokens: int = Field(512, description="")

    # Narration Generation Settings
    default_narration_model: str = Field("elevenlabs", description="")

    # Name
    name: str = Field(
        default="My Adventure",
        description="What is the name of the story?",
    )

    # Narrative settings
    narrative_tone: str = Field(
        default="silly",
        description="What is the narrative tone of the story? For example: silly, serious, gritty, etc.",
    )

    adventure_background: Optional[str] = Field(
        description="Description of the background setting in which the adventure will take place.  Can include descriptions of genre, characters, specific items and locations that exist in the world, references to real-world things, etc."
    )

    narrative_voice: Optional[str] = Field(
        description="What is the narrative voice of the adventure?  Some possibilities: children’s book, young adult novel, fanfic, high literature"
    )

    adventure_goal: str = Field(
        default="To rid the world of evil",
        description="What is the ultimate goal / motivation of this story?",
    )

    fixed_quest_arc: Optional[List[QuestDescription]] = Field(
        default=None,
        description="If you wish for your adventure to have a fixed set of quests, define them here.",
    )

    # Quest settings
    quests_per_arc: int = Field(
        default=10,
        description="How many quests must the player complete to finish the adventure?",
    )

    min_problems_per_quest: int = Field(
        default=2,
        description="""What is the minimum number of problems a player must solve to complete a quest?

Formula is (quest_no / problems_per_quest_scale) + min_problems_per_quest + randint(0, max_additional_problems_per_quest)""",
    )

    problems_per_quest_scale: float = Field(
        default=0.25,
        description="""How does the number of problems per quest scale with the quest # in sequence?

Formula is (quest_no / problems_per_quest_scale) + min_problems_per_quest + randint(0, max_additional_problems_per_quest)""",
    )

    max_additional_problems_per_quest: int = Field(
        default=2,
        description="""How many additional problems may be added randomly to a quest?

Formula is (quest_no / problems_per_quest_scale) + min_problems_per_quest + randint(0, max_additional_problems_per_quest)""",
    )

    problem_solution_difficulty: float = Field(
        default=1,
        description="""The difficulty scale factor applied to the LLM’s estimation of how likely a user’s solution is to solve the problem.  User’s random number between (0,1) must exceed the modified value to succeed.

Base Values:
VERY UNLIKELY=0.9
UNLIKELY = 0.7
LIKELY = 0.3
VERY LIKELY = 0.1

Difficulty modified value:
1 - ((1-BASE_VALUE) / problem_solution_difficulty)

Result - Doubling difficulty makes success 1/2 as likely; halving difficulty makes success twice as likely.""",
    )

    # Energy Management
    # NOTE: quest_cost is now set to zero becuase we're managing energy consumption from the web side of things.
    # TODO: Remove quest_cost entirely to reduce dead code?
    quest_cost: int = Field(0, description="The cost of going on one quest")

    camp_image_prompt: str = Field(
        "{tone} camp.",
        description="Prompt for generating camp images.",
    )

    # Narration settings
    narration_voice: AvailableVoice = Field(
        AvailableVoice.DOROTHY,
        description="The voice to use for narration of quest blocks",
    )

    # Image model settings

    camp_image_negative_prompt: str = Field(
        "",
        description="Negative prompt for generating camp images.",
    )

    item_image_prompt: str = Field(
        "16-bit retro-game style item in a hero's inventory. The items's name is: {name}. The item's description is: {description}.",
        description="Prompt for generating item images.",
    )

    item_image_negative_prompt: str = Field(
        "",
        description="Negative prompt for generating item images.",
    )

    profile_image_prompt: str = Field(
        "16-bit retro-game style profile picture of a hero on an adventure. The hero's name is: {name}. The hero has a description of: {description}.",
        description="Prompt for generating profile images.",
    )

    profile_image_negative_prompt: str = Field(
        "",
        description="Negative prompt for generating profile images.",
    )

    quest_background_image_prompt: str = Field(
        "16-bit background scene for a quest. The scene being depicted is: {description}",
        description="Prompt for generating quest background images.",
    )

    quest_background_image_negative_prompt: str = Field(
        "",
        description="Negative prompt for generating quest background images.",
    )

    scene_music_generation_prompt: str = Field(
        "16-bit game score for a quest game scene. {tone}. Scene description: {description}",
        description="The prompt used to generate music for a scene.  Game tone and scene description will be filled in as {tone} and {description}.",
    )

    camp_music_generation_prompt: str = Field(
        "background music for a quest game camp scene. {tone}.",
        description="The prompt used to generate music for camp.  Game tone will be filled in as {tone}.",
    )

    image_themes: List[StableDiffusionTheme] = Field(
        [], description="A list of stable diffusion themes to make available."
    )

    camp_image_theme: str = Field(
        "pixel_art_2",
        description="The Stable Diffusion theme for generating camp images.",
    )

    item_image_theme: str = Field(
        "pixel_art_2",
        description="The Stable Diffusion theme for generating item images.",
    )

    profile_image_theme: str = Field(
        "pixel_art_2",
        description="The Stable Diffusion theme for generating profile images.",
    )

    quest_background_theme: str = Field(
        "pixel_art_2",
        description="The Stable Diffusion theme for generating quest images.",
    )

    music_duration: int = Field(
        default=10,
        description="Length of music to generate in seconds. Must be less than 30.",
        le=30,
        ge=0,
    )

    @property
    def narration_voice_id(self) -> str:
        return _SUPPORTED_ELEVEN_VOICES.get(self.narration_voice.value).get("id")

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

        validation_errors = other.validate_prompts()
        if len(validation_errors) > 0:
            raise SteamshipError("\n".join(validation_errors))

        # Override values if they're present in the new version, but not in the old
        # Possible clobber here if the web doesn't send a value for a field with a default,
        # since it will be filled in when the ServerSettings object is init'd
        for k, v in other.dict().items():
            if v is not None:
                setattr(self, k, v)

    # Returns list of validation issues.
    def validate_prompts(self) -> List[str]:
        result = []
        result.append(
            validate_prompt_args(self.camp_image_prompt, ["tone"], "Camp image prompt")
        )
        result.append(
            validate_prompt_args(
                self.camp_image_negative_prompt, ["tone"], "Camp image negative prompt"
            )
        )
        result.append(
            validate_prompt_args(
                self.item_image_prompt, ["name", "description"], "Item image prompt"
            )
        )
        result.append(
            validate_prompt_args(
                self.item_image_negative_prompt,
                ["name", "description"],
                "Item image negative prompt",
            )
        )
        result.append(
            validate_prompt_args(
                self.profile_image_prompt,
                ["name", "description"],
                "Profile image prompt",
            )
        )
        result.append(
            validate_prompt_args(
                self.profile_image_prompt,
                ["name", "description"],
                "Profile image negative prompt",
            )
        )
        result.append(
            validate_prompt_args(
                self.quest_background_image_prompt,
                ["description"],
                "Quest background image prompt",
            )
        )
        result.append(
            validate_prompt_args(
                self.quest_background_image_prompt,
                ["description"],
                "Quest background image negative prompt",
            )
        )
        result.append(
            validate_prompt_args(
                self.scene_music_generation_prompt,
                ["tone", "description"],
                "Quest scene music prompt",
            )
        )
        result.append(
            validate_prompt_args(
                self.camp_music_generation_prompt,
                ["tone", "description"],
                "Camp music prompt",
            )
        )
        return [
            validation_error
            for validation_error in result
            if validation_error is not None
        ]
