import re
from enum import Enum
from typing import Any, Dict, List, Optional, Union, cast

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
        "value": "stable_diffusion_xl_no_loras",
        "label": "Stable Diffusion XL",
        "imageSample": "/image_samples/stable_diffusion_xl_no_loras.png",
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


def SettingField(  # noqa: N802
    default: Optional[Any],
    label: str,
    description: str,
    type: str,  # todo make enum
    listof: Optional[str] = None,  # todo make enum
    options: Optional[List[Dict]] = None,  # todo make inflated class
    include_dynamic_options: Optional[str] = None,  # TODO enum with image-themes
    required: Optional[bool] = None,
    unused: Optional[bool] = None,
    list_schema: Optional[List[Dict]] = None,  # how to represent this?
    requires_approval: Optional[bool] = None,
    required_text: Optional[str] = None,
    preview_output_type: Optional[
        str
    ] = None,  # TODO: This should eventually just be `supports_preview: bool`
    suggest_output_type: Optional[
        str
    ] = None,  # TODO: This should eventually just be `supports_suggestion: bool`
    approval_requested_field: Optional[str] = None,
    variables_permitted: Optional[Dict[str, str]] = None,
    onboarding_title: Optional[str] = None,
    onboarding_subtitle: Optional[str] = None,
    min: Optional[Union[int, float]] = None,
    max: Optional[Union[int, float]] = None,
    **kwargs,
) -> Any:
    """
    Pass along parameters into the pydantic-native way of expressing them while also expressing them as our schema type.
    `name` will be calculated from __fields__ later.
    """
    if "meta_setting" in kwargs:
        raise ValueError(
            "`meta_setting` is calculated, but was provided in arguments to SettingField."
        )

    # TODO do validations here against type, or possibly when we get the schema version on the class.
    # TODO can probably make a best-guess on label based on name, but that'd have to happen in post-process.
    # TODO can also probably make a best-guess on type based on variable type

    meta_setting = dict(  # noqa: C408
        label=label,
        description=description,
        type=type,  # todo probably.value when this is an enum
        default=default,
        listof=listof,
        options=options,
        includeDynamicOptions=include_dynamic_options,
        required=required,
        unused=unused,
        listSchema=list_schema,
        requiresApproval=requires_approval,
        requiredText=required_text,
        previewOutputType=preview_output_type,
        suggestOutputType=suggest_output_type,
        approvalRequestedField=approval_requested_field,
        variablesPermitted=variables_permitted,
        onboardingTitle=onboarding_title,
        onboardingSubtitle=onboarding_subtitle,
        min=min,
        max=max,
    )

    keep_nones_names = set(
        "default"
    )  # names of fields to keep in the dict when they're None
    meta_setting = {
        k: v for k, v in meta_setting.items() if v is not None or k in keep_nones_names
    }

    return Field(
        default=default,
        description=description,
        title=label,
        required=required,
        meta_setting=meta_setting,
        **kwargs,
    )


class ServerSettings(BaseModel):
    """Server Settings for the AI Adventure Game set by the Game Host.

    These are intended to be set by the game operator (not the user).
    """

    # Language Generation Settings - Function calling
    default_function_capable_llm_model: str = Field("gpt-3.5-turbo", description="")
    default_function_capable_llm_temperature: float = Field(0.0, description="")
    default_function_capable_llm_max_tokens: int = Field(512, description="")

    source_url: Optional[str] = Field(
        default=None,
        description="The URL from which this Adventure was generated. E.g. A URL to a short story on the web.",
    )

    source_story_text: Optional[str] = SettingField(
        default=None,
        label="Generate from Story",
        description="Optional. If you paste in a story or concept, we'll generate the adventure from that.",
        type="longtext",
    )

    image: Optional[str] = SettingField(
        default="",
        label="Image",
        description="Select an image to represent this adventure.",
        type="image",
        required=True,
        suggest_output_type="image",
        onboarding_title="Please upload or generate a title image.",
        onboarding_subtitle="This is like your movie poster. It will advertise your adventure to others.",
    )
    """For use on the profile marketing page and also during 'Magic Create' mode in the editor."""

    short_description: Optional[str] = SettingField(
        default="",
        label="Short Description",
        description="A catchy one-liner to help your adventure stand out in the discover page",
        type="text",
        required=True,
        suggest_output_type="short_description",
        onboarding_title="Please write a one-sentence description of your adventure.",
        onboarding_subtitle="This will help players understand what adventure they're about to play.",
    )

    description: Optional[str] = SettingField(
        default="",
        label="Description",
        description="A longer description of this adventure. Go into detail!",
        type="textarea",
        required=True,
        suggest_output_type="description",
        onboarding_title="Please write a more detailed description of your adventure.",
        onboarding_subtitle="The more detail you provide in your description, the more engaging your AI generated adventure will be.",
    )
    """For use on the profile marketing page and also during 'Magic Create' mode in the editor."""

    tags: Optional[List[Optional[str]]] = SettingField(
        default=None,
        label="Tags",
        description="A list of short string tags.",
        type="tag-list",
        listof="text",
    )
    """For use on the profile marketing page and also during 'Magic Create' mode in the editor."""

    # TODO what to do about this one?  It's not currently exported.
    characters: Optional[List[Optional[Character]]] = Field(
        default=None,
        description="The pre-made Characters one can play with this Adventure, for use on the profile marketing page and also during 'Magic Create' mode in the editor.",
    )
    """For use on the profile marketing page, during 'Magic Create' mode in the editor, and during onboarding."""

    # Language Generation Settings - Story telling
    default_story_model: str = SettingField(
        default="gpt-4-1106-preview",
        label="Story LLM Model",
        description="Model used to generate story text.",
        type="select",
        options=[
            {
                "value": "gpt-3.5-turbo",
                "label": "GPT 3.5 Turbo",
            },
            {
                "value": "gpt-4-1106-preview",
                "label": "GPT 4 turbo preview",
            },
            {
                "value": "gpt-4",
                "label": "GPT 4",
            },
        ],
    )
    default_story_temperature: float = SettingField(
        # NEEDS WORK:
        # TODO: Add a post-processing step to coerce this to a float.
        default=0.7,
        label="Story LLM Temperature",
        description="Temperature (creativity-factor) for the narrative generation. 0=Robot, 1=Bonkers, 0.4=Default",
        type="float",
        min=0,
        max=1,
    )
    default_story_max_tokens: int = SettingField(
        default=512,
        label="Story LLM Max Tokens",
        description="Maximum number of tokens permitted during generation.",
        type="int",
        min=0,
        max=2048,
    )

    # Narration Generation Settings
    default_narration_model: str = Field("elevenlabs", description="")

    # Name

    name: Optional[str] = SettingField(
        default="",
        label="Adventure Name",
        description="What name will others see this adventure by?",
        type="text",
        required=True,
        suggest_output_type="name",
        onboarding_title="What is the name of your adventure?",
        onboarding_subtitle="A short and catchy name will help your adventure stand out.",
    )

    # Narrative settings
    narrative_tone: str = SettingField(
        default="silly",
        label="Writing Style",
        description="What is the writing style of your story? E.g.: Written with drama and heavy intellectual dialogue, like Aaron Sorkin's West Wing.",
        type="text",
        required=True,
        suggest_output_type="narrative_tone",
        onboarding_title="What is the writing style you want to see?",
        onboarding_subtitle="References to specific and well known styles or storytellers will work best.",
    )

    adventure_background: Optional[str] = SettingField(
        default="A fantasy world",
        label="Adventure Background",
        suggest_output_type="adventure_background",
        description="""Description of the background setting in which the adventure will take place.

Can include descriptions of genre, characters, specific items and locations that exist in the world, references to real-world things, etc.""",
        type="longtext",
    )

    narrative_voice: Optional[str] = SettingField(
        default="young adult novel",
        label="Genre",
        description="What is the genre of your story? E.g.: children’s book, young adult novel, fanfic, high literature.",
        type="text",
        required=True,
        suggest_output_type="narrative_voice",
        onboarding_title="What is the genre of your adventure?",
        onboarding_subtitle="Selecting a short, evocative genre name will help generate a good adventure.",
    )

    generate_music: Optional[bool] = SettingField(
        default=False,
        label="Generate Music",
        description="Should this adventure generate music?",
        type="boolean",
        required=False,
    )

    adventure_goal: str = SettingField(
        default="To rid the world of evil",
        label="Adventure Goal",
        suggest_output_type="adventure_goal",
        description="What is the ultimate goal / motivation of this adventure?",
        type="longtext",
    )

    fixed_quest_arc: Optional[List[QuestDescription]] = SettingField(
        default=None,
        label="Fixed Quest Arc",
        description="Optional. If you wish for your adventure to have a fixed set of quests, define them here.",
        type="list",
        listof="object",
        suggest_output_type="fixed_quest_arc",
        onboarding_title="Create a series of quests for your adventure.",
        onboarding_subtitle="Adventures are comprised of a series of quests. Auto-generate a few you like -- you can edit them later!",
        list_schema=[
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
            {
                "name": "other_information",
                "label": "Other Information",
                "description": "Other information or instructions for the story of this quest, which will not be shown to the user.",
                "type": "longtext",
            },
            {
                "name": "challenges",
                "label": "Problems",
                "description": "Optional ordered list of problems that will be encountered on this quest.",
                "type": "list",
                "listof": "object",
                "listSchema": [
                    {
                        "name": "name",
                        "label": "Name",
                        "description": "Name of the problem.",
                        "type": "text",
                    },
                    {
                        "name": "description",
                        "label": "Description",
                        "description": "Describe the problem.",
                        "type": "longtext",
                    },
                ],
            },
            {
                "name": "items",
                "label": "Items",
                "description": "Optional item(s) that will be earned on this quest",
                "type": "list",
                "listof": "object",
                "listSchema": [
                    {
                        "name": "name",
                        "label": "Name",
                        "description": "Name of the item.",
                        "type": "text",
                    },
                    {
                        "name": "description",
                        "label": "Description",
                        "description": "Describe the item.",
                        "type": "longtext",
                    },
                ],
            },
        ],
        required=True,
    )

    # Quest settings
    quests_per_arc: int = SettingField(
        default=5,
        label="Quests per Arc",
        description="If you don't have a pre-defined list of quests, this is how many will be generated",
        type="int",
        min=1,
        max=10,
    )

    min_problems_per_quest: int = SettingField(
        default=2,
        label="Minimum Problems per Quest",
        description="What is the minimum number of problems a player must solve to complete a quest?",
        type="int",
        min=1,
        max=10,
    )

    problems_per_quest_scale: float = SettingField(
        default=0.25,
        label="Additional Problems per Quest Factor",
        description="A number between 0 and 1. The higher this is, the more additional problems a user will have to solve above the minimum.",
        type="float",
        min=0,
        max=1,
    )

    max_additional_problems_per_quest: int = SettingField(
        default=2,
        label="Maximum additional problems per quest",
        description="The maximum additional problems per quest that can be randomly added above and beyond the minimum required number.",
        type="int",
        min=1,
        max=5,
    )

    difficulty: Difficulty = SettingField(
        label="Problem Difficulty",
        default=Difficulty.NORMAL,
        description="""The difficulty factor applied to the AI’s estimation of how likely a user’s solution is to solve the problem. This affects required dice rolls.""",
        type="select",
        options=[
            {
                "value": "easy",
                "label": "Easy",
            },
            {
                "value": "normal",
                "label": "Normal",
            },
            {
                "value": "hard",
                "label": "Hard",
            },
        ],
    )

    # Energy Management
    # NOTE: quest_cost is now set to zero becuase we're managing energy consumption from the web side of things.
    # TODO: Remove quest_cost entirely to reduce dead code?
    quest_cost: int = Field(0, description="The cost of going on one quest")

    camp_image_prompt: str = SettingField(
        label="Camp Image Prompt",
        description="Prompt for generating the camp image.",
        type="longtext",
        default="{tone} {genre} camp.",
        variables_permitted={
            "tone": "Description of the tone of the adventure.",
            "genre": "Description of the genre of the adventure.",
        },
    )

    # Narration settings
    narration_multilingual: Optional[bool] = SettingField(
        default=False,
        label="Narration includes non-English",
        description="Set to true if the story include non-English content",
        type="boolean",
        required=False,
    )

    narration_voice: AvailableVoice = SettingField(
        default=AvailableVoice.DOROTHY,
        label="Narration Voice",
        description="Voice used to generate narration.",
        type="options",
        options=[
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
    )

    # Image model settings

    camp_image_negative_prompt: str = SettingField(
        label="Camp Image Negative Prompt",
        description="Negative prompt for generating camp images.",
        type="longtext",
        default="",
        variables_permitted={
            "tone": "Description of the tone of the adventure.",
            "genre": "Description of the genre of the adventure.",
        },
    )

    item_image_prompt: str = SettingField(
        label="Item Image Prompt",
        description="The prompt used to generate item images.",
        type="longtext",
        default="game sprite for an {name}, {description}",
        variables_permitted={
            "name": "The name of the item.",
            "description": "Description of the item.",
            "tone": "Description of the tone of the adventure.",
            "genre": "Description of the genre of the adventure.",
        },
    )

    item_image_negative_prompt: str = SettingField(
        label="Item Image Negative Prompt",
        description="The negative prompt for generating item images.",
        type="longtext",
        default="",
        variables_permitted={
            "name": "The name of the item.",
            "description": "Description of the item.",
            "tone": "Description of the tone of the adventure.",
            "genre": "Description of the genre of the adventure.",
        },
    )

    profile_image_prompt: str = SettingField(
        label="Profile Image Prompt",
        description="The prompt that will be used to generate the player's profile image.",
        type="longtext",
        default="close-up profile picture, focus on head, {name}, {description}",
        variables_permitted={
            "name": "The name of the character.",
            "description": "Description of the character.",
        },
    )

    profile_image_negative_prompt: str = SettingField(
        label="Profile Image Negative Prompt",
        description="The negative prompt for generating profile images.",
        type="longtext",
        default="",
        variables_permitted={
            "name": "The name of the character.",
            "tone": "Description of the tone of the adventure.",
            "genre": "Description of the genre of the adventure.",
            "description": "Description of the character.",
        },
    )

    quest_background_image_prompt: str = SettingField(
        label="Quest Background Prompt",
        description="The prompt for generating a quest background.",
        type="longtext",
        default="background scene for a quest. The scene being depicted is: {description}",
        variables_permitted={
            "tone": "Description of the tone of the adventure.",
            "genre": "Description of the genre of the adventure.",
            "description": "Description of the quest the player is on.",
        },
    )

    quest_background_image_negative_prompt: str = SettingField(
        name="quest_background_image_negative_prompt",
        label="Quest Background Negative Prompt",
        description="The negative prompt for generating quest background.",
        type="longtext",
        default="",
        variables_permitted={
            "tone": "Description of the tone of the adventure.",
            "genre": "Description of the genre of the adventure.",
            "description": "Description of the quest the player is on.",
        },
    )

    scene_music_generation_prompt: str = SettingField(
        label="Quest Music Prompt",
        description="The prompt used to generate music for a quest.  Game tone and scene description will be filled in as {tone} and {description}.",
        type="longtext",
        default="16-bit game score for a quest game scene. {tone}. Scene description: {description}",
        variables_permitted={
            "tone": "Description of the tone of the adventure.",
            "genre": "Description of the genre of the adventure.",
            "description": "Description of the quest the player is on.",
        },
    )

    camp_music_generation_prompt: str = SettingField(
        label="Camp Music Prompt",
        description="The prompt used to generate music for camp.  Game tone will filled in as {tone}.",
        type="longtext",
        default="background music for a quest game camp scene. {tone}.",
        variables_permitted={
            "tone": "Description of the tone of the adventure.",
            "genre": "Description of the genre of the adventure.",
            "description": "Description of the quest the player is on.",
        },
    )

    image_themes: List[Union[StableDiffusionTheme, DalleTheme]] = SettingField(
        default=[],
        label="Image Themes",
        description="Themes available to use in image generation. Reference these from the **Camp**, **Quests**, and **Items** settings pages.",
        type="list",
        listof="object",
        list_schema=[
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
    )

    generation_task_id: Optional[str] = Field(
        None,
        description="The ID of the generation task which represents the terminus of generating the agent's own configuration.",
    )

    adventure_image_theme: Optional[str] = SettingField(
        # VALIDATED
        label="Adventure Image Theme",
        description="Use a pre-made theme or add more in the **Image Themes** tab.",
        type="select",
        options=DEFAULT_THEMES,
        default="stable_diffusion_xl_no_loras",
        include_dynamic_options="image-themes",
    )

    camp_image_theme: str = SettingField(
        # VALIDATED
        label="Camp Image Theme",
        description="Use a pre-made theme or add more in the **Image Themes** tab.",
        type="select",
        options=DEFAULT_THEMES,
        default="pixel_art_1",
        include_dynamic_options="image-themes",
    )

    item_image_theme: str = SettingField(
        # VALIDATED
        label="Item Image Theme",
        description="Use a pre-made theme or add more in the **Image Themes** tab.",
        type="select",
        options=DEFAULT_THEMES,
        default="pixel_art_1",
        include_dynamic_options="image-themes",
    )

    profile_image_theme: str = SettingField(
        # VALIDATED
        label="Profile Image Theme",
        description="Use a pre-made theme or add more in the **Image Themes** tab.",
        type="select",
        options=DEFAULT_THEMES,
        default="pixel_art_1",
        include_dynamic_options="image-themes",
    )

    quest_background_theme: str = SettingField(
        # VALIDATED
        label="Quest Background Theme",
        description="Use a pre-made theme or add more in the **Image Themes** tab.",
        type="select",
        options=DEFAULT_THEMES,
        default="pixel_art_1",
        include_dynamic_options="image-themes",
    )

    game_engine_version: Optional[str] = SettingField(
        default=None,
        label="Game Engine Version",
        description="The version of the game engine to use",
        type="text",
    )

    music_duration: int = SettingField(
        default=10,
        max=30,
        min=0,
        label="Music Duration",
        description="Duration of music to generate. Default=10. Max=30. IMPORTANT: Values less than 15 are safest because generation takes so long.",
        type="int",
    )

    allowed_failures_per_quest: Optional[int] = SettingField(
        default=-1,
        label="Allowed Failures per Quest",
        description="If >= 0, the number of times the player is allowed to fail a die roll before they fail the quest.  If negative, quests don't fail due to failing too many die rolls.",
        type="int",
        max=10,
        min=-1,
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
        s = ServerSettings.schema_instance()

        result = []
        result.append(
            validate_prompt_args(
                self.camp_image_prompt,
                list(
                    (cast(dict, s.camp_image_prompt))
                    .get("variablesPermitted", {})
                    .keys()
                ),
                "Camp image prompt",
            )
        )
        result.append(
            validate_prompt_args(
                self.camp_image_negative_prompt,
                list(
                    (cast(dict, s.camp_image_negative_prompt))
                    .get("variablesPermitted", {})
                    .keys()
                ),
                "Camp image negative prompt",
            )
        )
        result.append(
            validate_prompt_args(
                self.item_image_prompt,
                list(
                    (cast(dict, s.item_image_prompt))
                    .get("variablesPermitted", {})
                    .keys()
                ),
                "Item image prompt",
            )
        )
        result.append(
            validate_prompt_args(
                self.item_image_negative_prompt,
                list(
                    (cast(dict, s.item_image_negative_prompt))
                    .get("variablesPermitted", {})
                    .keys()
                ),
                "Item image negative prompt",
            )
        )
        result.append(
            validate_prompt_args(
                self.profile_image_prompt,
                list(
                    (cast(dict, s.profile_image_prompt))
                    .get("variablesPermitted", {})
                    .keys()
                ),
                "Profile image prompt",
            )
        )
        result.append(
            validate_prompt_args(
                self.profile_image_negative_prompt,
                list(
                    (cast(dict, s.profile_image_negative_prompt))
                    .get("variablesPermitted", {})
                    .keys()
                ),
                "Profile image negative prompt",
            )
        )
        result.append(
            validate_prompt_args(
                self.quest_background_image_prompt,
                list(
                    (cast(dict, s.quest_background_image_prompt))
                    .get("variablesPermitted", {})
                    .keys()
                ),
                "Quest background image prompt",
            )
        )
        result.append(
            validate_prompt_args(
                self.quest_background_image_negative_prompt,
                list(
                    (cast(dict, s.quest_background_image_negative_prompt))
                    .get("variablesPermitted", {})
                    .keys()
                ),
                "Quest background image negative prompt",
            )
        )
        result.append(
            validate_prompt_args(
                self.scene_music_generation_prompt,
                list(
                    (cast(dict, s.scene_music_generation_prompt))
                    .get("variablesPermitted", {})
                    .keys()
                ),
                "Quest scene music prompt",
            )
        )
        result.append(
            validate_prompt_args(
                self.camp_music_generation_prompt,
                list(
                    (cast(dict, s.camp_music_generation_prompt))
                    .get("variablesPermitted", {})
                    .keys()
                ),
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
            result = {"name": field_name}
            meta_setting = field.field_info.extra.get("meta_setting")
            if not meta_setting:
                delattr(s, field_name)
                continue
            result.update(meta_setting)
            result["serverSetting"] = True
            setattr(s, field_name, result)
        return s
