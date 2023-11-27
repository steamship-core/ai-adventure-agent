from schema.server_settings import ServerSettings

s = ServerSettings.schema_instance()

GENERAL_OPTIONS = [
    {
        "name": "adventure_public",
        "label": "List in public directory",
        "description": "Check this box to list your adventure in the public directory.",
        "type": "boolean",
        "requiresApproval": True,
        "approvalRequestedField": "adventure_public_requested",
        "requiredText": "To make your adventure public and visible to the community, your account must be approved.",
    },
    s.name,
    s.short_description,
    s.description,
    s.tags,
    s.image,
    {
        "name": "adventure_player_singular_noun",
        "label": "Noun for a 'Player'",
        "description": "The singular noun used to refer to the pre-made player options. E.g.: Choose your Player (Adventurer, Hero, etc.)",
        "type": "text",
        "default": "Player",
    },
]

MAGIC_MODE_OPTIONS = [
    {
        "name": "adventure_name",
        "label": "Adventure Name",
        "description": "What name will others see this adventure by?",
        "type": "text",
        "default": "",
        "required": True,
        "suggestOutputType": "name",
    },
    {
        "name": "adventure_short_description",
        "label": "Short Description",
        "description": "A catchy one-liner to help your adventure stand out in the discover page",
        "type": "text",
        "default": "",
        "required": True,
        "suggestOutputType": "short_description",
    },
    {
        # Validated
        "name": "narrative_voice",
        "label": "Genre",
        "description": "What is the genre of your story? E.g.: children’s book, young adult novel, fanfic, high literature.",
        "type": "text",
        "default": "young adult novel",
        "suggestOutputType": "narrative_voice",
    },
    {
        # Validated
        "name": "narrative_tone",
        "label": "Writing Style",
        "description": "What is the writing style of your story? E.g.: Serious, Silly, Gritty, Film Noir, Heady, etc.",
        "type": "text",
        "default": "silly",
        "suggestOutputType": "narrative_tone",
    },
]


STORY_OPTIONS = [
    {
        "name": "story_general_divider",
        "label": "Storytelling Guidance",
        "description": "These settings will guide how the LLM generates your story.",
        "type": "divider",
    },
    s.narrative_voice,
    s.narrative_tone,
    s.adventure_background,
    s.adventure_goal,
    {
        "name": "quest_divider",
        "label": "Quests",
        "description": "Your adventure consists on a number of quests that the character must go on. You can either hand-create these quests or allow the LLM to generate them for each new player on the fly.",
        "type": "divider",
    },
    s.fixed_quest_arc,
    s.quests_per_arc,
    {
        "name": "problem_divider",
        "label": "Quest Problems",
        "description": "Each time a character goes on a quest, they encounter problems they must solve. These problems are generated by the LLM. The following settings control how the LLM generates these problems.",
        "type": "divider",
    },
    s.min_problems_per_quest,
    s.problems_per_quest_scale,
    s.max_additional_problems_per_quest,
    {
        # TODO: Validate float
        "name": "problem_solution_difficulty",
        "label": "Problem difficulty scale factor",
        "description": """The difficulty scale factor applied to the LLM’s estimation of how likely a user’s solution is to solve the problem.  User’s random number between (0,1) must exceed the modified value to succeed.

Base Values:
- VERY UNLIKELY=0.9
- UNLIKELY = 0.7
- LIKELY = 0.3
- VERY LIKELY = 0.1

Difficulty modified value:
1 - ((1-BASE_VALUE) / problem_solution_difficulty)

Result - Doubling difficulty makes success 1/2 as likely; halving difficulty makes success twice as likely.""",
        "type": "float",
        "default": 2,
        "min": 1,
    },
    {
        "name": "advanced_divider",
        "label": "Large Language Model Settings",
        "description": "These advanced settings control the LLM that generates your story.",
        "type": "divider",
    },
    s.default_story_model,
    s.default_story_temperature,
    s.default_story_max_tokens,
]

CHARACTER_OPTIONS = [
    {
        # Validated
        "name": "characters",
        "label": "Pre-made Characters",
        "description": "Each character you add here will be available to players staring a new game.",
        "type": "list",
        "listof": "object",
        "listSchema": [
            {
                "name": "name",
                "label": "Name",
                "description": "Name of the preset character.",
                "type": "text",
                "suggestOutputType": "name",
            },
            {
                "name": "image",
                "label": "Image",
                "description": "Image of the preset character.",
                "type": "image",
                "suggestOutputType": "image",
            },
            {
                "name": "tagline",
                "label": "Tag Line",
                "description": "A short tagline for your character.",
                "type": "text",
                "suggestOutputType": "tagline",
            },
            {
                "name": "description",
                "label": "Description",
                "description": "Description of the preset character. This influences gameplay.",
                "type": "longtext",
                "suggestOutputType": "description",
            },
            {
                "name": "background",
                "label": "Background",
                "description": "Background of the preset character. This influences gameplay.",
                "type": "longtext",
                "suggestOutputType": "background",
            },
        ],
    },
]


IMAGE_OPTIONS = [
    {
        "type": "divider",
        "name": "profile-divider",
        "label": "Profile Images",
        "description": "Set the theme and prompt for generating player profile images.",
        "previewOutputType": "profile_image",
    },
    s.profile_image_theme,
    s.profile_image_prompt,
    s.profile_image_negative_prompt,
    {
        "type": "divider",
        "name": "item-divider",
        "label": "Item Images",
        "description": "Set the theme and prompt for generating images for items found on quests.",
        "previewOutputType": "item_image",
    },
    s.item_image_theme,
    s.item_image_prompt,
    s.item_image_negative_prompt,
    {
        "type": "divider",
        "name": "camp-divider",
        "label": "Camp Images",
        "description": "Set the theme and prompt for generating images for the camp background.",
        "previewOutputType": "camp_image",
    },
    s.camp_image_theme,
    s.camp_image_prompt,
    s.camp_image_negative_prompt,
    {
        "type": "divider",
        "name": "quest-divider",
        "label": "Quest Images",
        "description": "Set the theme and prompt for generating in-quest images.",
        "previewOutputType": "scene_image",
    },
    s.quest_background_theme,
    s.quest_background_image_prompt,
    s.quest_background_image_negative_prompt,
]

VOICE_OPTIONS = [s.narration_voice]

MUSIC_OPTIONS = [
    s.scene_music_generation_prompt,
    s.camp_music_generation_prompt,
    s.music_duration,
]

IMAGE_THEME_OPTIONS = [s.image_themes]

GAME_ENGINE_OPTIONS = [
    {
        "name": "game_engine_version",
        "label": "Version",
        "description": "Game engine version this Adventure should use. Only values of the form `ai-adventure@VERSION` will be saved. Replace VERSION with the desired version.",
        "type": "upgrade-offer",
        "default": "",
    }
]

SCHEMA = [
    {
        "spacer": True,
        "title": "General",
    },
    {
        "title": "General Settings",
        "description": "Settings for your game.",
        "href": "general-settings",
        "settings": GENERAL_OPTIONS,
    },
    {
        "title": "Auto Generate",
        "description": "Generate an entire game from scratch.",
        "href": "magic-mode",
        "settings": [],
    },
    {
        "spacer": True,
        "title": "Game",
    },
    {
        "title": "Story",
        "description": "The quests and challenges for your adventure.",
        "href": "story-options",
        "settings": STORY_OPTIONS,
    },
    {
        "title": "Characters",
        "description": "Offer pre-made characters to your game players.",
        "href": "character-options",
        "settings": CHARACTER_OPTIONS,
    },
    {
        "title": "Images",
        "description": "Control the generation of your story's images.",
        "href": "image-options",
        "settings": IMAGE_OPTIONS,
    },
    {
        "title": "Voices",
        "description": "Settings that control your story's voice narration.",
        "href": "voice-options",
        "settings": VOICE_OPTIONS,
    },
    {
        "title": "Music",
        "description": "Settings that control your story's music generation.",
        "href": "music-options",
        "settings": MUSIC_OPTIONS,
    },
    {
        "spacer": True,
        "title": "Advanced",
    },
    {
        "title": "Image Themes",
        "description": "Create stable diffusion themes for image generation.",
        "href": "image-themes",
        "settings": IMAGE_THEME_OPTIONS,
    },
    {
        "title": "Game Engine",
        "description": "The AI Agent hosted on Steamship.com powering the game.",
        "href": "game-engine",
        "settings": GAME_ENGINE_OPTIONS,
    },
    {
        "title": "Import",
        "description": "Import an entire adventure template at once by pasting exported YAML and clicking Save.",
        "href": "import",
    },
    {
        "title": "Export",
        "description": "Save or share your adventure settings by copying this block of YAML code.",
        "href": "export",
    },
]
