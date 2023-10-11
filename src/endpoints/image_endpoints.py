from typing import List, Optional

from steamship import Block, PluginInstance, Steamship, Tag
from steamship.agents.schema import AgentContext
from steamship.data import TagValueKey
from steamship.invocable import post
from steamship.invocable.package_mixin import PackageMixin

from utils.agent_service import AgentService
from utils.context_utils import get_game_state, get_profile_image_generator
from utils.tags import CharacterTag, TagKindExtensions


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
