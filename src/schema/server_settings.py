import re
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field
from steamship import SteamshipError

from schema.characters import Character
from schema.image_theme import DalleTheme, StableDiffusionTheme
from schema.quest import QuestDescription


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


class Difficulty(str, Enum):
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"


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


DEFAULT_THEMES = [
    {
        "value": "pixel_art_1",
        "label": "Pixel Art 1 (Stable Diffusion)",
        "imageSample": "/image_samples/pixel_art_1.png",
    },
    {
        "value": "pixel_art_2",
        "label": "Pixel Art 2 (Stable Diffusion)",
        "imageSample": "/image_samples/pixel_art_2.png",
    },
    {
        "value": "pixel_art_3",
        "label": "Pixel Art 3 (Stable Diffusion)",
        "imageSample": "/image_samples/pixel_art_3.png",
    },
    {
        "value": "dall_e_2_standard",
        "label": "DALL-E 2",
        "imageSample": "/image_samples/dall_e_2_standard.png",
    },
    {
        "value": "dall_e_2_stellar_dream",
        "label": "Stellar Dream (DALL-E 2)",
        "imageSample": "/image_samples/dall_e_2_stellar_dream.png",
    },
    {
        "value": "dall_e_2_neon_cyberpunk",
        "label": "Neon Cyberpunk (DALL-E 2)",
        "imageSample": "/image_samples/dall_e_2_neon_cyberpunk.png",
    },
    {
        "value": "cinematic_animation",
        "label": "Outdoor Fantasy Painting (Stable Diffusion)",
        "imageSample": "/image_samples/cinematic_animation.jpeg",
    },
]


class ServerSettings(BaseModel):
    """Server Settings for the AI Adventure Game set by the Game Host.

    These are intended to be set by the game operator (not the user).
    """

    @classmethod
    def setting_schema(cls, name: str) -> Dict[str, Any]:
        field = cls.__fields__.get(name)
        if not field:
            raise AttributeError(f"No field named {name}")
        meta_setting = field.field_info.extra.get("meta_setting")
        if not meta_setting:
            raise AttributeError(f"Field {name} has no setting schema")
        # See TODO on name
        # meta_setting["default"] = field.default
        meta_setting["serverSetting"] = True
        return meta_setting

    # Language Generation Settings - Function calling
    default_function_capable_llm_model: str = Field("gpt-3.5-turbo", description="")
    default_function_capable_llm_temperature: float = Field(0.0, description="")
    default_function_capable_llm_max_tokens: int = Field(512, description="")

    source_url: Optional[str] = Field(
        default=None,
        description="The URL from which this Adventure was generated. E.g. A URL to a short story on the web.",
    )

    source_story_text: Optional[str] = Field(
        default=None,
        description="The short story text which this Adventure originates. This data is necessary during 'Magic Create' mode in the editor, but can be removed afterward.",
    )

    image: Optional[str] = Field(
        default=None,
        meta_setting={
            "name": "image",
            "label": "Image",
            "description": "Select an image to represent this adventure.",
            "type": "image",
            "default": "",
            "required": True,
            "suggestOutputType": "image",
        },
    )
    """For use on the profile marketing page and also during 'Magic Create' mode in the editor."""

    short_description: Optional[str] = Field(
        default="An amazing story of exploration.",
        meta_setting={
            "name": "adventure_short_description",
            "label": "Short Description",
            "description": "A catchy one-liner to help your adventure stand out in the discover page",
            "type": "text",
            "default": "",
            "required": True,
            "suggestOutputType": "short_description",
        },
    )

    description: Optional[str] = Field(
        default="An amazing story of exploration.",
        meta_setting={
            "name": "description",
            "label": "Description",
            "description": "A longer description of this adventure. Go into detail!",
            "type": "textarea",
            "default": "",
            "required": True,
            "suggestOutputType": "description",
        },
    )
    """For use on the profile marketing page and also during 'Magic Create' mode in the editor."""

    tags: Optional[List[Optional[str]]] = Field(
        default=None,
        meta_setting={
            "name": "tags",
            "label": "Tags",
            "description": "A list of short string tags.",
            "type": "tag-list",
            "listof": "text",
        },
    )
    """For use on the profile marketing page and also during 'Magic Create' mode in the editor."""

    characters: Optional[List[Optional[Character]]] = Field(
        default=None,
        description="The pre-made Characters one can play with this Adventure, for use on the profile marketing page and also during 'Magic Create' mode in the editor.",
    )
    """For use on the profile marketing page, during 'Magic Create' mode in the editor, and during onboarding."""

    # Language Generation Settings - Story telling
    default_story_model: str = Field(
        "gpt-3.5-turbo",
        meta_setting={
            # Validated
            "name": "default_story_model",
            "label": "Story LLM Model",
            "description": "Model used to generate story text.",
            "type": "select",
            "default": "gpt-3.5-turbo",
            "options": [
                {
                    "value": "gpt-3.5-turbo",
                    "label": "GPT 3.5 Turbo",
                },
                {
                    "value": "gpt-4",
                    "label": "GPT 4",
                },
            ],
        },
    )
    default_story_temperature: float = Field(
        0.7,
        meta_setting={
            # NEEDS WORK:
            # TODO: Add a post-processing step to coerce this to a float.
            "name": "default_story_temperature",
            "label": "Story LLM Temperature",
            "description": "Temperature (creativity-factor) for the narrative generation. 0=Robot, 1=Bonkers, 0.4=Default",
            "type": "float",
            "default": 0.7,
        },
    )
    default_story_max_tokens: int = Field(
        512,
        meta_setting={
            # NEEDS WORK:
            # TODO: Add a post-processing step to coerce this to an int.
            "name": "default_story_max_tokens",
            "label": "Story LLM Max Tokens",
            "description": "Maximum number of tokens permitted during generation. 256=Default",
            "type": "int",
            "default": 512,
        },
    )

    # Narration Generation Settings
    default_narration_model: str = Field("elevenlabs", description="")

    # Name
    name: Optional[str] = Field(
        # TODO default is duplicated here, because I haven't thought through the scenario of what it defaults to on the
        #  agent vs the UI yet
        default="My Adventure",
        meta_setting={
            "name": "name",
            "label": "Adventure Name",
            "description": "What name will others see this adventure by?",
            "type": "text",
            "default": "",
            "required": True,
            "suggestOutputType": "name",
        },
    )

    short_description: Optional[str] = Field(
        default="An amazing story of exploration.",
        meta_setting={
            "name": "short_description",
            "label": "Short Description",
            "description": "A catchy one-liner to help your adventure stand out in the discover page",
            "type": "text",
            "default": "",
            "required": True,
            "suggestOutputType": "short_description",
        },
    )

    # Narrative settings
    narrative_tone: str = Field(
        default="silly",
        meta_setting={
            # Validated
            "name": "narrative_tone",
            "label": "Writing Style",
            "description": "What is the writing style of your story? E.g.: Serious, Silly, Gritty, Film Noir, Heady, etc.",
            "type": "text",
            "default": "silly",
            "suggestOutputType": "narrative_tone",
        },
    )

    adventure_background: Optional[str] = Field(
        meta_setting={
            # Validated
            "name": "adventure_background",
            "label": "Adventure Background",
            "description": """Description of the background setting in which the adventure will take place.

Can include descriptions of genre, characters, specific items and locations that exist in the world, references to real-world things, etc.""",
            "type": "longtext",
            "default": "A fantasy world",
            "suggestOutputType": "adventure_background",
        },
    )

    narrative_voice: Optional[str] = Field(
        meta_setting={
            # Validated
            "name": "narrative_voice",
            "label": "Genre",
            "description": "What is the genre of your story? E.g.: children’s book, young adult novel, fanfic, high literature.",
            "type": "text",
            "default": "young adult novel",
            "suggestOutputType": "narrative_voice",
        },
    )

    adventure_goal: str = Field(
        default="To rid the world of evil",
        meta_setting={
            # Validated
            "name": "adventure_goal",
            "label": "Adventure Goal",
            "description": "What is the ultimate goal / motivation of this adventure?",
            "type": "longtext",
            "default": "To rid the world of evil",
            "suggestOutputType": "adventure_goal",
        },
    )

    fixed_quest_arc: Optional[List[QuestDescription]] = Field(
        default=None,
        meta_setting={
            # VALIDATED
            "name": "fixed_quest_arc",
            "label": "Fixed Quest Arc",
            "description": "Optional. If you wish for your adventure to have a fixed set of quests, define them here.",
            "type": "list",
            "listof": "object",
            "listSchema": [
                # TODO FUTURE this could be pulled directly from QuestDescription
                {
                    "name": "goal",
                    "label": "Goal",
                    "description": "The goal of the quest.",
                    "type": "text",
                },
                {
                    "name": "location",
                    "label": "Location",
                    "description": "The location of the quest.",
                    "type": "text",
                },
                {
                    "name": "description",
                    "label": "Description",
                    "description": "Optional description of the quest's desired characteristics.",
                    "type": "longtext",
                },
            ],
        },
    )

    # Quest settings
    quests_per_arc: int = Field(
        default=10,
        meta_setting={
            # TODO: Validate int
            "name": "quests_per_arc",
            "label": "Quests per Arc",
            "description": "If you don't have a pre-defined list of quests, this is how many will be generated",
            "type": "int",
            "default": 10,
        },
    )

    min_problems_per_quest: int = Field(
        default=2,
        meta_setting={
            # TODO: Validate int
            "name": "min_problems_per_quest",
            "label": "Minimum Problems per Quest",
            "description": "What is the minimum number of problems a player must solve to complete a quest?",
            "type": "int",
            "default": 2,
            "min": 1,
        },
    )

    problems_per_quest_scale: float = Field(
        default=0.25,
        meta_setting={
            # TODO: Validate int
            "name": "problems_per_quest_scale",
            "label": "Additional Problems per Quest Factor",
            "description": "A number between 0 and 1. The higher this is, the more additional problems a user will have to solve above the minimum.",
            "type": "float",
            "default": 0.25,
            "min": 0,
        },
    )

    max_additional_problems_per_quest: int = Field(
        default=2,
        meta_setting={
            # TODO: Validate int
            "name": "max_additional_problems_per_quest",
            "label": "Maximum additional problems per quest",
            "description": "The maximum additional problems per quest that can be randomly added above and beyond the minimum required number.",
            "type": "int",
            "default": 2,
            "min": 1,
        },
    )

    # TODO (PR) this is different than problem_solution_difficulty, is this getting used?
    difficulty: Difficulty = Field(
        default=Difficulty.NORMAL,
        description="""The difficulty factor applied to the AI’s estimation of how likely a user’s solution is to solve the problem. This affects required dice rolls.""",
    )

    # Energy Management
    # NOTE: quest_cost is now set to zero becuase we're managing energy consumption from the web side of things.
    # TODO: Remove quest_cost entirely to reduce dead code?
    quest_cost: int = Field(0, description="The cost of going on one quest")

    camp_image_prompt: str = Field(
        "{tone} camp.",
        meta_setting={
            # VALIDATED
            "name": "camp_image_prompt",
            "label": "Camp Image Prompt",
            "description": "Prompt for generating the camp image.",
            "type": "longtext",
            "default": "{tone} {genre} camp.",
            "variablesPermitted": {
                "tone": "Description of the tone of the adventure.",
                "genre": "Description of the genre of the adventure.",
            },
        },
    )

    # Narration settings
    narration_voice: AvailableVoice = Field(
        AvailableVoice.DOROTHY,
        meta_setting={
            # VALIDATED
            "name": "narration_voice",
            "label": "Narration Voice",
            "description": "Voice used to generate narration.",
            "type": "options",
            "default": "adam",
            # TODO FUTURE like listObject this could be populated from the enum, theoretically
            "options": [
                {
                    "value": "dorothy",
                    "audioSample": "dorothy",
                    "label": "Dorothy",
                    "description": "British woman with a clear voice for storytelling.",
                },
                {
                    "value": "knightly",
                    "audioSample": "knightly",
                    "label": "Knightly",
                    "description": "Old British man. A deep and smooth voice for storytelling and podcast.",
                },
                {
                    "value": "oswald",
                    "audioSample": "oswald",
                    "label": "Oswald",
                    "description": "Intelligent Professor.",
                },
                {
                    "value": "marcus",
                    "audioSample": "marcus",
                    "label": "Marcus",
                    "description": "An authoritative and deep voice. Great for audio books or news.",
                },
                {
                    "value": "bria",
                    "audioSample": "bria",
                    "label": "Bria",
                    "description": "A young female with a softly spoken tone, perfect for storytelling or ASMR.",
                },
                {
                    "value": "alex",
                    "audioSample": "alex",
                    "label": "Alex",
                    "description": "Young american man. Is a strong and expressive narrator.",
                },
                {
                    "value": "valentino",
                    "audioSample": "valentino",
                    "label": "Valentino",
                    "description": "A great voice with depth. The voice is deep with a great accent, and works well for meditations.",
                },
                {
                    "value": "natasha",
                    "audioSample": "natasha",
                    "label": "Natasha",
                    "description": "A valley girl female voice. Great for shorts.",
                },
                {
                    "value": "brian",
                    "audioSample": "brian",
                    "label": "Brian",
                    "description": "Great voice for nature documentaries.",
                },
                {
                    "value": "joanne",
                    "audioSample": "joanne",
                    "label": "Joanne",
                    "description": "Young american woman. A soft and pleasant voice for a great character.",
                },
            ],
        },
    )

    # Image model settings

    camp_image_negative_prompt: str = Field(
        "",
        description="Negative prompt for generating camp images.",
        meta_setting={
            # VALIDATED
            "name": "camp_image_negative_prompt",
            "label": "Camp Image Negative Prompt",
            "description": "Negative prompt for generating camp images.",
            "type": "longtext",
            "default": "",
            "variablesPermitted": {
                "tone": "Description of the tone of the adventure.",
                "genre": "Description of the genre of the adventure.",
            },
        },
    )

    generation_task_id: str = Field(
        "",
        description="The ID of the generation task which represents the terminus of generating the agent's own configuration.",
    )

    item_image_prompt: str = Field(
        "16-bit retro-game style item in a hero's inventory. The items's name is: {name}. The item's description is: {description}.",
        description="Prompt for generating item images.",
        meta_setting={
            "name": "item_image_prompt",
            "label": "Item Image Prompt",
            "description": "The prompt used to generate item images.",
            "type": "longtext",
            "default": "16-bit retro-game sprite for an {name}, {description}",
            "variablesPermitted": {
                "name": "The name of the item.",
                "description": "Description of the item.",
            },
        },
    )

    item_image_negative_prompt: str = Field(
        "",
        meta_setting={
            # VALIDATED
            "name": "item_image_negative_prompt",
            "label": "Item Image Negative Prompt",
            "description": "The negative prompt for generating item images.",
            "type": "longtext",
            "default": "",
            "variablesPermitted": {
                "name": "The name of the item.",
                "description": "Description of the item.",
            },
        },
    )

    profile_image_prompt: str = Field(
        "16-bit retro-game style profile picture of a hero on an adventure. The hero's name is: {name}. The hero has a description of: {description}.",
        meta_setting={
            # VALIDATED
            "name": "profile_image_prompt",
            "label": "Profile Image Prompt",
            "description": "The prompt that will be used to generate the player's profile image.",
            "type": "longtext",
            "default": "close-up profile picture, focus on head, {name}, {description}",
            "variablesPermitted": {
                "name": "The name of the character.",
                "description": "Description of the character.",
            },
        },
    )

    profile_image_negative_prompt: str = Field(
        "",
        meta_setting={
            # VALIDATED
            "name": "profile_image_negative_prompt",
            "label": "Profile Image Negative Prompt",
            "description": "The negative prompt for generating profile images.",
            "type": "longtext",
            "default": "",
            "variablesPermitted": {
                "name": "The name of the character.",
                "description": "Description of the character.",
            },
        },
    )

    quest_background_image_prompt: str = Field(
        "16-bit background scene for a quest. The scene being depicted is: {description}",
        meta_setting={
            # VALIDATED
            "name": "quest_background_image_prompt",
            "label": "Quest Background Prompt",
            "description": "The prompt for generating a quest background.",
            "type": "longtext",
            "default": "16-bit background scene for a quest. The scene being depicted is: {description}",
            "variablesPermitted": {
                "description": "Description of the quest the player is on.",
            },
        },
    )

    quest_background_image_negative_prompt: str = Field(
        "",
        meta_setting={
            # VALIDATED
            "name": "quest_background_image_negative_prompt",
            "label": "Quest Background Negative Prompt",
            "description": "The negative prompt for generating quest background.",
            "type": "longtext",
            "default": "",
            "variablesPermitted": {
                "description": "Description of the quest the player is on.",
            },
        },
    )

    scene_music_generation_prompt: str = Field(
        "16-bit game score for a quest game scene. {tone}. Scene description: {description}",
        meta_setting={
            # VALIDATED
            "name": "scene_music_generation_prompt",
            "label": "Quest Music Prompt",
            "description": "The prompt used to generate music for a quest.  Game tone and scene description will be filled in as {tone} and {description}.",
            "type": "longtext",
            "default": "16-bit game score for a quest game scene. {tone}. Scene description: {description}",
        },
    )

    camp_music_generation_prompt: str = Field(
        "background music for a quest game camp scene. {tone}.",
        meta_setting={
            # VALIDATED
            "name": "camp_music_generation_prompt",
            "label": "Camp Music Prompt",
            "description": "The prompt used to generate music for camp.  Game tone will filled in as {tone}.",
            "type": "longtext",
            "default": "background music for a quest game camp scene. {tone}.",
        },
    )

    image_themes: List[Union[StableDiffusionTheme, DalleTheme]] = Field(
        [],
        meta_setting={
            # VALIDATED
            "name": "image_themes",
            "label": "Image Themes",
            "description": "Themes available to use in image generation. Reference these from the **Camp**, **Quests**, and **Items** settings pages.",
            "type": "list",
            "listof": "object",
            "listSchema": [
                {
                    "name": "name",
                    "label": "Name",
                    "description": "Name of the theme.",
                    "type": "text",
                },
                {
                    "name": "prompt_prefix",
                    "label": "Prompt Prefix",
                    "description": "Any extra words, including trigger words for LoRAs in this theme. Include a comma and spacing if you require it.",
                    "type": "longtext",
                },
                {
                    "name": "prompt_suffix",
                    "label": "Prompt Suffix",
                    "description": "Any extra words, including trigger words for LoRAs in this theme. Include a command and spacing if you require it.",
                    "type": "longtext",
                },
                {
                    "name": "negative_prompt_prefix",
                    "label": "Negative Prompt Prefix",
                    "description": "Any extra words, including trigger words for LoRAs in this theme. Include a comma and spacing if you require it.",
                    "type": "longtext",
                },
                {
                    "name": "negative_prompt_suffix",
                    "label": "Negative Prompt Suffix",
                    "description": "Any extra words, including trigger words for LoRAs in this theme. Include a command and spacing if you require it.",
                    "type": "longtext",
                },
                {
                    "name": "model",
                    "label": "Generation Model",
                    "description": "Which model to use.",
                    "type": "select",
                    "options": [
                        {
                            "label": "Stable Diffusion 1.5",
                            "value": "runwayml/stable-diffusion-v1-5",
                        },
                        {
                            "label": "Stable Diffusion XL 1.0",
                            "value": "stabilityai/stable-diffusion-xl-base-1.0",
                        },
                    ],
                },
                {
                    "name": "loras",
                    "label": "Loras",
                    "description": "List of LoRAs to use for image generation",
                    "type": "list",
                    "listof": "text",
                },
                {
                    "name": "seed",
                    "label": "Random Seed",
                    "description": "The same seed and prompt passed to the same version of StableDiffusion will output the same image every time.",
                    "type": "int",
                    "default": -1,
                },
                {
                    "name": "num_inference_steps",
                    "label": "Num Inference Steps",
                    "description": "Increasing the number of steps tells Stable Diffusion that it should take more steps to generate your final result which can increase the amount of detail in your image.",
                    "type": "int",
                    "default": 30,
                },
                {
                    "name": "guidance_scale",
                    "label": "Guidance Scale",
                    "description": "The CFG(Classifier Free Guidance) scale is a measure of how close you want the model to stick to your prompt when looking for a related image to show you.",
                    "type": "float",
                    "default": 7.5,
                },
                {
                    "name": "clip_skip",
                    "label": "Clip Skip",
                    "description": "Skips part of the image generation process, leading to slightly different results. This means the image renders faster, too.",
                    "type": "int",
                    "default": 0,
                },
                {
                    "name": "scheduler",
                    "label": "Scheduler",
                    "description": "Scheduler (or sampler) to use for the image denoising process.",
                    "type": "select",
                    "options": [
                        {
                            "label": "DPM++ 2M",
                            "value": "DPM++ 2M",
                        },
                        {
                            "label": "DPM++ 2M Karras",
                            "value": "DPM++ 2M Karras",
                        },
                        {
                            "label": "DPM++ 2M SDE",
                            "value": "DPM++ 2M SDE",
                        },
                        {
                            "label": "DPM++ 2M SDE Karras",
                            "value": "DPM++ 2M SDE Karras",
                        },
                        {
                            "label": "Euler",
                            "value": "Euler",
                        },
                        {
                            "label": "Euler A",
                            "value": "Euler A",
                        },
                    ],
                },
            ],
        },
    )

    camp_image_theme: str = Field(
        "pixel_art_2",
        meta_setting={
            # VALIDATED
            "name": "camp_image_theme",
            "label": "Camp Image Theme",
            "description": "Use a pre-made theme or add more in the **Image Themes** tab.",
            "type": "select",
            "options": DEFAULT_THEMES,
            "default": "pixel_art_1",
            "includeDynamicOptions": "image-themes",
        },
    )

    item_image_theme: str = Field(
        "pixel_art_2",
        meta_setting={
            # VALIDATED
            "name": "item_image_theme",
            "label": "Item Image Theme",
            "description": "Use a pre-made theme or add more in the **Image Themes** tab.",
            "type": "select",
            "options": DEFAULT_THEMES,
            "default": "pixel_art_1",
            "includeDynamicOptions": "image-themes",
        },
    )

    profile_image_theme: str = Field(
        "pixel_art_2",
        meta_setting={
            # VALIDATED
            "name": "profile_image_theme",
            "label": "Profile Image Theme",
            "description": "Use a pre-made theme or add more in the **Image Themes** tab.",
            "type": "select",
            "options": DEFAULT_THEMES,
            "default": "pixel_art_1",
            "includeDynamicOptions": "image-themes",
        },
    )

    quest_background_theme: str = Field(
        "pixel_art_2",
        meta_setting={
            # VALIDATED
            "name": "quest_background_theme",
            "label": "Quest Background Theme",
            "description": "Use a pre-made theme or add more in the **Image Themes** tab.",
            "type": "select",
            "options": DEFAULT_THEMES,
            "default": "pixel_art_1",
            "includeDynamicOptions": "image-themes",
        },
    )

    music_duration: int = Field(
        default=10,
        description="Length of music to generate in seconds. Must be less than 30.",
        le=30,
        ge=0,
        meta_setting={
            # VALIDATED
            "name": "music_duration",
            "label": "Music Duration",
            "description": "Duration of music to generate. Default=10. Max=30. IMPORTANT: Values less than 15 are safest because generation takes so long.",
            "type": "int",
            "default": 10,
        },
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
        for k, _ in other.dict().items():
            # Note: this preserves the types of inner objects.
            v = getattr(other, k)
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

    @classmethod
    def schema_instance(cls) -> "ServerSettings":
        """
        Create a new ServerSettings instance but then replace the values with their definitions, in wild defiance of
        type checking.  But... Field/FieldInfo does that anyway, right?
        :return: ServerSettings, but with fields replaced with their schema instead of value.
        """
        s = cls()
        for field_name, field in cls.__fields__.items():
            meta_setting = field.field_info.extra.get("meta_setting")
            if not meta_setting:
                delattr(s, field_name)
                continue
            meta_setting["serverSetting"] = True
            setattr(s, field_name, meta_setting)
        return s
