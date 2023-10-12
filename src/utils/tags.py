from enum import Enum


class TagKindExtensions(str, Enum):
    # This tag is of the kind "scene" which contains information about a media scene.
    SCENE = "scene"

    # This tag is of the kind "character" which contains information about a character.
    CHARACTER = "character"

    # This tag contains information about the overall tone / setting of the story
    STORY_CONTEXT = "story_context"

    QUEST = "quest"

    # This tag is of the kind "item" which contains information about an item.
    ITEM = "item"


class AgentStatusMessageTag(str, Enum):
    # The quest is complete
    QUEST_COMPLETE = "quest-complete"


class SceneTag(str, Enum):
    # A scene has started
    START = "start"

    # A scene has ended
    END = "end"

    # A scene background is being described
    BACKGROUND = "background"

    # The scene's background audio is being described
    AUDIO = "audio"

    # A narration block is being provided.
    # TODO: Should we reference WHICH block it narrates in the value? That
    # way it can be attached to the right block in the UI.
    NARRATION = "narration"


class CharacterTag(str, Enum):
    # The character's image is being replaced with a new one
    IMAGE = "image"

    BACKGROUND = "background"

    DESCRIPTION = "description"

    INVENTORY = "inventory"

    MOTIVATION = "motivation"

    NAME = "name"


class StoryContextTag(str, Enum):

    GENRE = "genre"

    TONE = "tone"


class QuestTag(str, Enum):

    QUEST_CONTENT = "quest_content"
    QUEST_PROMPT = "quest_prompt"
    USER_SOLUTION = "user_solution"
    QUEST_ID = "quest_id"
    QUEST_SUMMARY = "quest_summary"

class ItemTag(str, Enum):
    IMAGE = "image"
    NAME = "name"
