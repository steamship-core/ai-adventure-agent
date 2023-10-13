from typing import Final, List, Optional

from steamship import Block, PluginInstance, Steamship, Tag
from steamship.agents.schema import AgentContext
from steamship.invocable import post
from steamship.invocable.package_mixin import PackageMixin

from utils.agent_service import AgentService
from utils.context_utils import get_background_music_generator, get_game_state
from utils.tags import SceneTag, TagKindExtensions


class MusicMixin(PackageMixin):
    """Provides endpoints for Image generation."""

    GENERATE_SCENE_PATH: Final[str] = "generate_scene_music"
    client: Steamship
    agent_service: AgentService

    def __init__(self, client: Steamship, agent_service: AgentService):
        self.client = client
        self.agent_service = agent_service

    def _generate_music(
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

    @post(GENERATE_SCENE_PATH)
    def generate_scene_music(
        self, description: str, context_id: Optional[str] = None, **kwargs
    ) -> Block:

        context = self.agent_service.build_default_context(context_id=context_id)
        game_state = get_game_state(context)
        genre = game_state.genre or "Adventure"
        tone = game_state.tone or "Triumphant"

        prompt = f"16-bit game score for a quest game scene. {genre} genre. {tone}. Scene description: {description}"

        plugin = get_background_music_generator(context=context)
        tags = [
            Tag(kind=TagKindExtensions.SCENE, name=SceneTag.AUDIO),
        ]
        if quest_id := game_state.current_quest:
            tags.append(Tag(kind=TagKindExtensions.QUEST, name=quest_id))

        return self._generate_music(
            prompt=prompt,
            plugin=plugin,
            tags=tags,
            context=context,
            **kwargs,
        )
