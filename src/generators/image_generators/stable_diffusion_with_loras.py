import json
import time
from typing import Final

from steamship import Tag, Task, TaskState
from steamship.agents.schema import AgentContext
from steamship.data import TagValueKey

from generators.image_generator import ImageGenerator
from schema.objects import Item
from utils.context_utils import get_game_state
from utils.tags import CharacterTag, ItemTag, SceneTag, TagKindExtensions


def _await_task_running(task: Task) -> Task:
    while task.state in [TaskState.waiting]:
        time.sleep(0.1)
        task.refresh()
    return task


class StableDiffusionWithLorasImageGenerator(ImageGenerator):

    PLUGIN_HANDLE: Final[str] = "fal-sd-lora-image-generator-streaming"

    def request_item_image_generation(self, item: Item, context: AgentContext) -> Task:
        # TODO(doug): cache plugin instance by client workspace
        sd = context.client.use_plugin(
            StableDiffusionWithLorasImageGenerator.PLUGIN_HANDLE
        )

        game_state = get_game_state(context)

        item_prompt = (
            f"(pixel art) 16-bit retro-game sprite for an item in a hero's inventory. "
            f"The items's name is: {item.name}. "
            f"The item's description is: {item.description}. "
        )

        tags = [
            Tag(kind=TagKindExtensions.ITEM, name=ItemTag.IMAGE),
            Tag(
                kind=TagKindExtensions.ITEM,
                name=ItemTag.NAME,
                value={TagValueKey.STRING_VALUE: item.name},
            ),
        ]
        if quest_id := game_state.current_quest:
            tags.append(Tag(kind=TagKindExtensions.QUEST, name=quest_id))

        options = {
            "seed": game_state.preferences.seed,
            "image_size": "square",
            "loras": json.dumps(
                [{"path": "https://civitai.com/api/download/models/135931"}]
            ),
        }

        return _await_task_running(
            sd.generate(
                text=item_prompt,
                tags=tags,
                streaming=True,
                append_output_to_file=True,
                output_file_id=context.chat_history.file.id,
                make_output_public=True,
                options=options,
            )
        )

    def request_profile_image_generation(self, context: AgentContext) -> Task:
        # TODO(doug): cache plugin instance by client workspace
        sd = context.client.use_plugin(
            StableDiffusionWithLorasImageGenerator.PLUGIN_HANDLE
        )

        game_state = get_game_state(context)
        name = game_state.player.name
        description = game_state.player.description
        background = game_state.player.background

        profile_prompt = (
            f"(pixel art) 16-bit retro-game style profile picture of a hero on an adventure. "
            f"The hero's name is: {name}. "
            f"The hero has the following background: {background}. "
            f"The hero has a description of: {description}. "
        )

        tags = [
            Tag(kind=TagKindExtensions.CHARACTER, name=CharacterTag.IMAGE),
            Tag(
                kind=TagKindExtensions.CHARACTER,
                name=CharacterTag.NAME,
                value={TagValueKey.STRING_VALUE: name},
            ),
        ]
        if quest_id := game_state.current_quest:
            tags.append(Tag(kind=TagKindExtensions.QUEST, name=quest_id))

        options = {
            "seed": game_state.preferences.seed,
            "image_size": "portrait_4_3",
            "loras": json.dumps(
                [{"path": "https://civitai.com/api/download/models/135931"}]
            ),
        }

        return _await_task_running(
            sd.generate(
                text=profile_prompt,
                tags=tags,
                streaming=True,
                append_output_to_file=True,
                output_file_id=context.chat_history.file.id,
                make_output_public=True,
                options=options,
            )
        )

    def request_scene_image_generation(
        self, description: str, context: AgentContext
    ) -> Task:
        # TODO(doug): cache plugin instance by client workspace
        sd = context.client.use_plugin(
            StableDiffusionWithLorasImageGenerator.PLUGIN_HANDLE
        )
        game_state = get_game_state(context)

        scene_prompt = (
            "(pixel art) background scene for a quest. \n"
            "The scene being depicted is: \n"
            f"{description}"
        )

        tags = [
            Tag(kind=TagKindExtensions.SCENE, name=SceneTag.BACKGROUND),
        ]
        if quest_id := game_state.current_quest:
            tags.append(Tag(kind=TagKindExtensions.QUEST, name=quest_id))

        options = {
            "seed": game_state.preferences.seed,
            "image_size": "square_hd",
            "loras": json.dumps(
                [{"path": "https://civitai.com/api/download/models/135931"}]
            ),
        }

        return _await_task_running(
            sd.generate(
                text=scene_prompt,
                tags=tags,
                streaming=True,
                append_output_to_file=True,
                output_file_id=context.chat_history.file.id,
                make_output_public=True,
                options=options,
            )
        )
