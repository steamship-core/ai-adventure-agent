import json
from typing import Final

from steamship import Tag, Task
from steamship.agents.schema import AgentContext
from steamship.data import TagValueKey

from generators import utils
from generators.image_generator import ImageGenerator
from generators.utils import safe_format
from schema.objects import Item
from utils.context_utils import get_game_state, get_server_settings
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

    PLUGIN_HANDLE: Final[str] = "fal-sd-lora-image-generator-streaming"

    def request_item_image_generation(self, item: Item, context: AgentContext) -> Task:
        # TODO(doug): cache plugin instance by client workspace
        sd = context.client.use_plugin(
            StableDiffusionWithLorasImageGenerator.PLUGIN_HANDLE
        )

        game_state = get_game_state(context)
        server_settings = get_server_settings(context)

        item_prompt = safe_format(
            server_settings.item_image_prompt,
            {
                "genre": game_state.genre or "Adventure",
                "tone": game_state.tone or "Triumphant",
                "name": item.name or "A random object",
                "description": item.description or "Of usual character",
            },
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
            "loras": json.dumps(
                map(lambda lora: {"path": lora}, server_settings.item_image_loras)
            ),
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
        server_settings = get_server_settings(context)

        name = game_state.player.name
        description = game_state.player.description
        background = game_state.player.background

        profile_prompt = safe_format(
            server_settings.profile_image_prompt,
            {
                "genre": game_state.genre or "Adventure",
                "tone": game_state.tone or "Triumphant",
                "name": name or "Hero",
                "description": description or "A superhero that will save the day.",
                "background": background or "From humble beginnings.",
            },
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
            "loras": json.dumps(
                map(lambda lora: {"path": lora}, server_settings.profile_image_loras)
            ),
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
        server_settings = get_server_settings(context)

        scene_prompt = safe_format(
            server_settings.quest_background_image_prompt,
            {
                "genre": game_state.genre or "Adventure",
                "tone": game_state.tone or "Triumphant",
                "description": description or "An interesting place far away.",
            },
        )

        tags = [
            Tag(kind=TagKindExtensions.SCENE, name=SceneTag.BACKGROUND),
        ]
        if quest_id := game_state.current_quest:
            tags.append(QuestIdTag(quest_id))

        options = {
            "seed": game_state.preferences.seed,
            "image_size": "landscape_16_9",
            "loras": json.dumps(
                map(
                    lambda lora: {"path": lora},
                    server_settings.quest_background_image_loras,
                )
            ),
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
        server_settings = get_server_settings(context)

        scene_prompt = safe_format(
            server_settings.camp_image_prompt,
            {
                "genre": game_state.genre or "Adventure",
                "tone": game_state.tone or "Triumphant",
            },
        )

        tags = [
            Tag(kind=TagKindExtensions.STORY_CONTEXT, name=StoryContextTag.CAMP),
            Tag(kind=TagKindExtensions.CAMP, name=CampTag.IMAGE),
        ]

        options = {
            "seed": game_state.preferences.seed,
            "image_size": "landscape_16_9",
            "loras": json.dumps(
                map(lambda lora: {"path": lora}, server_settings.camp_image_loras)
            ),
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
