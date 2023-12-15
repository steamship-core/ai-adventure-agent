from enum import Enum

from steamship import Tag


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

    MERCHANT = "merchant"

    # This tag is of the kind "camp" which contains information about camp.
    CAMP = "camp"

    QUEST_ARC = "quest_arc"

    # This tag is used to identify a set of instructions for a portion of the story
    INSTRUCTIONS = "instructions"

    # This tag is used to identify the token count for a block
    TOKEN_COUNT = "token_count"  # noqa: S105


class AgentStatusMessageTag(str, Enum):
    # The quest is complete
    QUEST_COMPLETE = "quest-complete"

    # The quest has failed
    QUEST_FAILED = "quest-failed"


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

    INTRODUCTION = "introduction"
    INTRODUCTION_PROMPT = "introduction_prompt"


class StoryContextTag(str, Enum):
    TONE = "tone"
    CAMP = "camp"
    BACKGROUND = "background"
    VOICE = "voice"


class QuestTag(str, Enum):
    QUEST_CONTENT = "quest_content"
    QUEST_PROMPT = "quest_prompt"
    ACTION_CHOICES_PROMPT = "action_choices_prompt"
    ACTION_CHOICES = "action_choices"
    USER_SOLUTION = "user_solution"
    QUEST_ID = "quest_id"
    QUEST_SUMMARY = "quest_summary"
    ITEM_GENERATION_CONTENT = "item_generation_content"
    ITEM_GENERATION_PROMPT = "item_generation_prompt"
    LIKELIHOOD_EVALUATION = "likelihood_evaluation"
    DICE_ROLL = "dice_roll"


class ItemTag(str, Enum):
    IMAGE = "image"
    NAME = "name"


class MerchantTag(str, Enum):
    INVENTORY = "inventory"
    INVENTORY_GENERATION_PROMPT = "inventory_generation_prompt"


class CampTag(str, Enum):
    AUDIO = "audio"
    IMAGE = "image"


class QuestIdTag(Tag):
    @staticmethod
    def matches(tag: Tag, quest_id: str):
        if tag.kind == TagKindExtensions.QUEST and tag.name == QuestTag.QUEST_ID:
            if tag.value is not None:
                if tag.value.get("id").lower() == quest_id.lower():
                    return True
        return False

    def __init__(self, quest_id: str):
        super().__init__(
            kind=TagKindExtensions.QUEST, name=QuestTag.QUEST_ID, value={"id": quest_id}
        )


class QuestArcTag(str, Enum):
    PROMPT = "prompt"
    RESULT = "result"


class InstructionsTag(str, Enum):
    ONBOARDING = "onboarding"
    QUEST = "quest"
