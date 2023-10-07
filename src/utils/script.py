import json
import logging
from typing import List, Optional, Union

from context_utils import (
    get_audio_narration_generator,
    get_background_image_generator,
    get_background_music_generator,
    get_story_text_generator,
)
from steamship import Block, MimeTypes, Steamship, Tag, Task
from steamship.agents.schema import AgentContext
from steamship.agents.schema.chathistory import ChatHistory
from steamship.data.operations.generator import GenerateResponse
from steamship.data.tags import TagValueKey
from tags import CharacterTag, SceneTag, TagKindExtensions

from schema.quest import Quest
from schema.server_settings import ServerSettings


class Script(ChatHistory):
    """
    TODO: Doug notes that many of these are "File Centric" methods.. when perhaps what
    we want are Tool-centric objects.

    E.g. why not ChangeSceneTool, SetMusicTool

    That way a human could still call them.. but so too could a bot.
    """

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

    def generate_background_image(
        self, prompt: str, context: AgentContext
    ) -> List[Block]:
        """game developer perspective:

        script.generate_sound_effect("dsf")
        script.generate_background_image("In a dark forest, you see a castle in the distance.", context)
        script.generate_background_image("This", context)
        """

        generator = get_background_image_generator(context)
        _ = generator.generate(
            text=prompt,
            append_output_to_file=True,
            output_file_id=self.file.id,
            make_output_public=True,
            streaming=True,
        )
        # self.emit_blocks(task.output.blocks, context)
        # return task.output.blocks
        return []

    def generate_background_music(
        self, prompt: str, context: AgentContext
    ) -> List[Block]:
        generator = get_background_music_generator(context)
        _ = generator.generate(
            text=prompt,
            append_output_to_file=True,
            output_file_id=self.file.id,
            make_output_public=True,
            streaming=True,
        )
        # self.emit_blocks(task.output.blocks, context)
        # return task.output.blocks
        return []

    def generate_narration(
        self, block: Block, context: AgentContext
    ) -> Task[GenerateResponse]:
        generator = get_audio_narration_generator(context)
        task = generator.generate(
            text=block.text,
            append_output_to_file=True,
            output_file_id=self.file.id,
            make_output_public=True,
            streaming=True,
        )
        return task

    def generate_story(self, prompt: str, context: AgentContext) -> Block:
        BASE_TAGS = [
            Tag(
                kind="request-id",
                name=context.request_id,
                value={TagValueKey.STRING_VALUE.value: context.request_id},
            )
        ]
        generator = get_story_text_generator(context)
        self.append_system_message(prompt)
        generated_text = generator.generate(self.file.id).wait().blocks[0].text
        block = self.append_assistant_message(generated_text, tags=BASE_TAGS)
        # self.emit_blocks([block], context)
        return block

    def end_scene(self, quest: Quest, context: AgentContext):
        BASE_TAGS = [
            Tag(
                kind="request-id",
                name=context.request_id,
                value={TagValueKey.STRING_VALUE.value: context.request_id},
            )
        ]
        print("Ending scene", quest)
        self.file.append_block(
            text=json.dumps(quest.dict()),
            mime_type=MimeTypes.JSON,
            tags=[
                BASE_TAGS,
                Tag(kind=TagKindExtensions.SCENE.value, name=SceneTag.END.value),
            ],
        )

    def emit_blocks(self, blocks: List[Block], context: AgentContext):
        # TODO: Can we have a web collector emit func?
        for func in context.emit_funcs:
            logging.info(
                f"Emitting via function '{func.__name__}' for context: {context.id}"
            )
            func(blocks, context.metadata)


# Character Action
# Scene Change
# Narration
# Item Found

if __name__ == "__main__":
    client = Steamship()
    context = AgentContext.get_or_create(client, {"id": "FOOOO"})
    script = Script(context.chat_history)
    settings = ServerSettings()
    settings.add_to_agent_context(context)
    block = script.generate_story("Hi", context)
    print(block)
    narration = script.generate_narration(block, context)
    print(narration)