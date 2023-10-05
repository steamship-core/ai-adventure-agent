from enum import Enum


class TagKindExtensions(str, Enum):
    # This tag is of the kind "script" which contains information about a media scene.
    SCENE = "scene"

    # This tag is of the kind "character" which contains information about a character.
    CHARACTER = "character"


class SceneTag(str, Enum):
    # A scene has started
    START = "start"

    # A scene has ended
    END = "end"

    # A scene backround is being described
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
