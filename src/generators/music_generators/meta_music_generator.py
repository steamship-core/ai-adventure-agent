from typing import Final

from steamship import Tag, Task
from steamship.agents.schema import AgentContext

from generators import utils
from generators.music_generator import MusicGenerator
from utils.context_utils import get_game_state
from utils.tags import SceneTag, TagKindExtensions


class MetaMusicGenerator(MusicGenerator):
    PLUGIN_HANDLE: Final[str] = "music-generator-streaming"

    def request_scene_music_generation(self, description: str, context: AgentContext) -> Task:
        music_gen = context.client.use_plugin(self.PLUGIN_HANDLE)
        game_state = get_game_state(context)
        genre = game_state.genre or "Adventure"
        tone = game_state.tone or "Triumphant"

        prompt = f"16-bit game score for a quest game scene. {genre} genre. {tone}. Scene description: {description}"

        tags = [
            Tag(kind=TagKindExtensions.SCENE, name=SceneTag.AUDIO),
        ]
        if quest_id := game_state.current_quest:
            tags.append(Tag(kind=TagKindExtensions.QUEST, name=quest_id))

        num_existing_blocks = len(context.chat_history.file.blocks)
        task = music_gen.generate(
            text=prompt,
            append_output_to_file=True,
            streaming=True,
            output_file_id=context.chat_history.file.id,
            make_output_public=True,
            tags=tags,
        )
        # this has obvious flaw but hopefully that corner case is small enough
        return utils.await_blocks_created_and_task_started(num_existing_blocks, context.chat_history.file, task)

