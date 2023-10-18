import json
from typing import Dict, Final, Optional

from pydantic.fields import PrivateAttr
from steamship import Tag, Task
from steamship.agents.schema import AgentContext
from steamship.data import TagValueKey

from generators import utils
from generators.image_generator import ImageGenerator
from schema.objects import Item
from utils.context_utils import get_game_state
from utils.tags import (
    CampTag,
    CharacterTag,
    ItemTag,
    QuestIdTag,
    SceneTag,
    StoryContextTag,
    TagKindExtensions,
)


class StableDiffusionWithLorasImageGenerator(ImageGenerator):

    PLUGIN_HANDLE: Final[str] = "fal-sd-lora-image-generator"
    DEFAULT_LORA: Final[str] = "https://civitai.com/api/download/models/123593"
    KNOWN_LORAS_AND_TRIGGERS: Final[Dict[str, str]] = {
        # Pixel Art XL (https://civitai.com/models/120096/pixel-art-xl) by https://civitai.com/user/NeriJS
        "https://civitai.com/api/download/models/135931": "(pixel art)",
        # Pixel Art SDXL RW (https://civitai.com/models/114334/pixel-art-sdxl-rw) by https://civitai.com/user/leonnn1
        "https://civitai.com/api/download/models/123593": "((pixelart))",
    }

    _lora: str = PrivateAttr(default=DEFAULT_LORA)

    def __init__(self, lora: Optional[str] = DEFAULT_LORA):
        super().__init__()
        self._lora = lora

    def request_item_image_generation(self, item: Item, context: AgentContext) -> Task:
        # TODO(doug): cache plugin instance by client workspace
        sd = context.client.use_plugin(
            StableDiffusionWithLorasImageGenerator.PLUGIN_HANDLE
        )

        game_state = get_game_state(context)

        item_prompt = (
            f"{StableDiffusionWithLorasImageGenerator.KNOWN_LORAS_AND_TRIGGERS[self._lora]} "
            "16-bit retro-game style item in a hero's inventory. "
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
            tags.append(QuestIdTag(quest_id))

        options = {
            "seed": game_state.preferences.seed,
            "image_size": "square_hd",
            "loras": json.dumps([{"path": self._lora}]),
        }

        num_existing_blocks = len(context.chat_history.file.blocks)
        task = sd.generate(
            text=item_prompt,
            tags=tags,
            streaming=True,
            append_output_to_file=True,
            output_file_id=context.chat_history.file.id,
            make_output_public=True,
            options=options,
        )

        # this has obvious flaw but hopefully that corner case is small enough
        return utils.await_blocks_created_and_task_started(
            num_existing_blocks,
            context.chat_history.file,
            task,
            new_block_tag_kind=TagKindExtensions.ITEM,
            new_block_tag_name=ItemTag.IMAGE,
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
            f"{StableDiffusionWithLorasImageGenerator.KNOWN_LORAS_AND_TRIGGERS[self._lora]} "
            "16-bit retro-game style profile picture of a hero on an adventure. "
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
            tags.append(QuestIdTag(quest_id))

        options = {
            "seed": game_state.preferences.seed,
            "image_size": "portrait_4_3",
            "loras": json.dumps([{"path": self._lora}]),
        }

        num_existing_blocks = len(context.chat_history.file.blocks)
        task = sd.generate(
            text=profile_prompt,
            tags=tags,
            streaming=True,
            append_output_to_file=True,
            output_file_id=context.chat_history.file.id,
            make_output_public=True,
            options=options,
        )

        # this has obvious flaw but hopefully that corner case is small enough
        updated_task = utils.await_blocks_created_and_task_started(
            num_existing_blocks,
            context.chat_history.file,
            task,
            new_block_tag_kind=TagKindExtensions.CHARACTER,
            new_block_tag_name=CharacterTag.IMAGE,
        )
        return updated_task

    def request_scene_image_generation(
        self, description: str, context: AgentContext
    ) -> Task:
        # TODO(doug): cache plugin instance by client workspace
        sd = context.client.use_plugin(
            StableDiffusionWithLorasImageGenerator.PLUGIN_HANDLE
        )
        game_state = get_game_state(context)

        scene_prompt = (
            f"{StableDiffusionWithLorasImageGenerator.KNOWN_LORAS_AND_TRIGGERS[self._lora]} "
            "16-bit background scene for a quest. The scene being depicted is: \n"
            f"{description}"
        )

        tags = [
            Tag(kind=TagKindExtensions.SCENE, name=SceneTag.BACKGROUND),
        ]
        if quest_id := game_state.current_quest:
            tags.append(QuestIdTag(quest_id))

        options = {
            "seed": game_state.preferences.seed,
            "image_size": "landscape_16_9",
            "loras": json.dumps([{"path": self._lora}]),
        }

        num_existing_blocks = len(context.chat_history.file.blocks)
        task = sd.generate(
            text=scene_prompt,
            tags=tags,
            streaming=True,
            append_output_to_file=True,
            output_file_id=context.chat_history.file.id,
            make_output_public=True,
            options=options,
        )

        # this has obvious flaw but hopefully that corner case is small enough
        return utils.await_blocks_created_and_task_started(
            num_existing_blocks,
            context.chat_history.file,
            task,
            new_block_tag_kind=TagKindExtensions.SCENE,
            new_block_tag_name=SceneTag.BACKGROUND,
        )

    def request_camp_image_generation(self, context: AgentContext) -> Task:
        # TODO(doug): cache plugin instance by client workspace
        sd = context.client.use_plugin(
            StableDiffusionWithLorasImageGenerator.PLUGIN_HANDLE
        )
        game_state = get_game_state(context)

        scene_prompt = (
            f"{StableDiffusionWithLorasImageGenerator.KNOWN_LORAS_AND_TRIGGERS[self._lora]} "
            f"{game_state.tone} {game_state.genre} camp."
        )

        tags = [
            Tag(kind=TagKindExtensions.STORY_CONTEXT, name=StoryContextTag.CAMP),
            Tag(kind=TagKindExtensions.CAMP, name=CampTag.IMAGE),
        ]

        options = {
            "seed": game_state.preferences.seed,
            "image_size": "landscape_16_9",
            "loras": json.dumps([{"path": self._lora}]),
        }

        num_existing_blocks = len(context.chat_history.file.blocks)
        task = sd.generate(
            text=scene_prompt,
            tags=tags,
            streaming=True,
            append_output_to_file=True,
            output_file_id=context.chat_history.file.id,
            make_output_public=True,
            options=options,
        )

        # this has obvious flaw but hopefully that corner case is small enough
        return utils.await_blocks_created_and_task_started(
            num_known_blocks=num_existing_blocks,
            file=context.chat_history.file,
            task=task,
            new_block_tag_kind=TagKindExtensions.CAMP,
            new_block_tag_name=CampTag.IMAGE,
        )
