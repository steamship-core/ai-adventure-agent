from typing import List, Optional, Union

from steamship import MimeTypes
from steamship.agents.schema.chathistory import ChatHistory
from steamship.data import Block
from steamship.data.tags import Tag

from game_agent.tags import CharacterTag, SceneTag, TagKindExtensions


class Script(ChatHistory):
    def __init__(self, chat_history: ChatHistory):
        super().__init__(
            file=chat_history.file,
            embedding_index=chat_history.embedding_index,
            text_splitter=chat_history.text_splitter,
        )

    def append_scene_action(
        self,
        name: SceneTag,
        text: str = None,
        tags: List[Tag] = None,
        content: Union[str, bytes] = None,
        url: Optional[str] = None,
        mime_type: Optional[MimeTypes] = None,
    ) -> Block:
        tags = tags or []
        tags.append(Tag(kind=TagKindExtensions.SCENE, name=name))
        if not text and not content and not url:
            text = "{}"
            mime_type = MimeTypes.JSON

        block = self.file.append_block(
            text=text, tags=tags, content=content, url=url, mime_type=mime_type
        )
        return block

    def append_character_action(
        self,
        name: CharacterTag,
        text: str = None,
        tags: List[Tag] = None,
        content: Union[str, bytes] = None,
        url: Optional[str] = None,
        mime_type: Optional[MimeTypes] = None,
    ) -> Block:
        tags = tags or []
        tags.append(Tag(kind=TagKindExtensions.CHARACTER, name=name))
        if not text and not content and not url:
            text = "{}"
            mime_type = MimeTypes.JSON

        block = self.file.append_block(
            text=text, tags=tags, content=content, url=url, mime_type=mime_type
        )
        return block


# Character Action
# Scene Change
# Narration
# Item Found
