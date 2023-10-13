import logging
from typing import List, Optional

from steamship import Block, MimeTypes, PluginInstance, Steamship, SteamshipError, Tag
from steamship.agents.schema import AgentContext
from steamship.data import TagValueKey
from steamship.data.block import StreamState
from steamship.invocable import post
from steamship.invocable.package_mixin import PackageMixin

from utils.agent_service import AgentService
from utils.context_utils import (
    get_background_image_generator,
    get_game_state,
    get_item_image_generator,
    get_profile_image_generator,
)
from utils.tags import CharacterTag, ItemTag, SceneTag, TagKindExtensions


class ImageMixin(PackageMixin):
    """Provides endpoints for Image generation."""

    client: Steamship
    agent_service: AgentService

    def __init__(self, client: Steamship, agent_service: AgentService):
        self.client = client
        self.agent_service = agent_service

    def _generate_image(
        self,
        prompt: str,
        plugin: PluginInstance,
        context: AgentContext,
        tags: Optional[List[Tag]] = None,
        **kwargs,
    ) -> Block:
        task = plugin.generate(
            text=prompt,
            append_output_to_file=True,
            output_file_id=context.chat_history.file.id,
            make_output_public=True,
            tags=tags,
        )
        task.wait_until_completed()
        return task.output.blocks[0]

    @post("/generate_profile_image")
    def generate_profile_image(
        self, context_id: Optional[str] = None, **kwargs
    ) -> Block:
        """Generate a profile image for a character.

        Image will be saved to the chat history of the agent context, as well as returned directly.
        """
        # TODO: should we include inventory items maybe?
        context = self.agent_service.build_default_context(context_id=context_id)
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

        image_plugin = get_profile_image_generator(context=context)
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

        return self._generate_image(
            prompt=profile_prompt,
            plugin=image_plugin,
            tags=tags,
            context=context,
            **kwargs,
        )

    @post("/generate_item_image")
    def generate_item_image(
        self,
        item_name: str,
        item_description: str,
        context_id: Optional[str] = None,
        **kwargs,
    ) -> Block:
        """Generate an image for an item.

        Image will be saved to the chat history of the agent context, as well as returned directly.
        """
        # TODO: should we include inventory items maybe?
        context = self.agent_service.build_default_context(context_id=context_id)
        game_state = get_game_state(context)

        # TODO(dougreid): should this only be invoked once the inventory is saved?
        item = None
        for player_item in game_state.player.inventory:
            if player_item.name == item_name:
                item = player_item

        if item is None:
            logging.error(f"could not find item in player inventory: {item}")
        #    raise SteamshipError(f"could not find item '{item_name}' for player.")

        item_prompt = (
            f"(pixel art) 16-bit retro-game sprite for an item in a hero's inventory. "
            f"The items's name is: {item_name}. "
            f"The item's description is: {item_description}. "
        )

        image_plugin = get_item_image_generator(context=context)
        tags = [
            Tag(kind=TagKindExtensions.ITEM, name=ItemTag.IMAGE),
            Tag(
                kind=TagKindExtensions.ITEM,
                name=ItemTag.NAME,
                value={TagValueKey.STRING_VALUE: item_name},
            ),
        ]
        if quest_id := game_state.current_quest:
            tags.append(Tag(kind=TagKindExtensions.QUEST, name=quest_id))

        logging.info("calling _generate_image")
        item_block = self._generate_image(
            prompt=item_prompt,
            plugin=image_plugin,
            tags=tags,
            context=context,
            **kwargs,
        )

        # TODO: can't save game state here, as it may get saved in another context ?
        # item.picture_url = item_block.to_public_url()
        # save_game_state(game_state, context)

        logging.info(f"generated an item image: {item_block.id}")
        return item_block

    @post("/generate_background_image")
    def generate_background_image(
        self,
        description: str,
        context_id: Optional[str] = None,
        **kwargs,
    ) -> Block:
        """Generate an image for the background of a scene.

        Image will be saved to the chat history of the agent context, as well as returned directly.
        """
        context = self.agent_service.build_default_context(context_id=context_id)
        game_state = get_game_state(context)

        scene_prompt = (
            "(pixel art) background scene for a quest. \n"
            "The scene being depicted is: \n"
            f"{description}"
        )

        image_plugin = get_background_image_generator(context=context)
        tags = [
            Tag(kind=TagKindExtensions.SCENE, name=SceneTag.BACKGROUND),
        ]
        if quest_id := game_state.current_quest:
            tags.append(Tag(kind=TagKindExtensions.QUEST, name=quest_id))

        return self._generate_image(
            prompt=scene_prompt,
            plugin=image_plugin,
            tags=tags,
            context=context,
            **kwargs,
        )

    @post("/generate_background_image_existing_block")
    def generate_background_image_existing_block(
        self,
        block_id: str,
        description: str,
        context_id: Optional[str] = None,
        **kwargs,
    ) -> Block:
        background_block = self.generate_background_image(
            description=description, context_id=context_id, **kwargs
        )
        try:
            streaming_block = Block.get(client=self.client, _id=block_id)
            if not streaming_block:
                raise SteamshipError("um, we are going to need a block here...")
            if streaming_block.stream_state not in [StreamState.STARTED]:
                raise SteamshipError("um, this block better set up for streaming yo")
            streaming_block.append_stream(background_block.raw())
            streaming_block.finish_stream()

            # TODO: update block with tags
            return streaming_block
        except SteamshipError as e:
            raise e
        except Exception as e:
            raise SteamshipError(f"could not generate image into block: {e}")

    def preallocate_scene_block(
        self, context_id: Optional[str] = None, **kwargs
    ) -> Block:
        context = self.agent_service.build_default_context(context_id=context_id)
        game_state = get_game_state(context)

        tags = [
            Tag(kind=TagKindExtensions.SCENE, name=SceneTag.BACKGROUND),
        ]
        if quest_id := game_state.current_quest:
            tags.append(Tag(kind=TagKindExtensions.QUEST, name=quest_id))

        return Block.create(
            client=self.client,
            file_id=context.chat_history.file.id,
            public_data=True,
            mime_type=MimeTypes.PNG,  # this seems dangerous, but leave it for now...
            tags=tags,
            streaming=True,
        )
