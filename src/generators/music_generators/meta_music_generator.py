from typing import Final

from steamship import Tag, Task
from steamship.agents.schema import AgentContext

from generators import utils
from generators.music_generator import MusicGenerator
from generators.utils import safe_format
from utils.context_utils import get_game_state, get_server_settings
from utils.tags import CampTag, QuestIdTag, SceneTag, StoryContextTag, TagKindExtensions


class MetaMusicGenerator(MusicGenerator):
    PLUGIN_HANDLE: Final[str] = "music-generator"

    def request_scene_music_generation(
        self, description: str, context: AgentContext
    ) -> Task:
        music_gen = context.client.use_plugin(self.PLUGIN_HANDLE)
        game_state = get_game_state(context)
        server_settings = get_server_settings(context)

        prompt = safe_format(
            server_settings.music_prompt,
            {
                "genre": game_state.genre or "Adventure",
                "tone": game_state.tone or "Triumphant",
                "description": description,
            },
        )

        tags = [
            Tag(kind=TagKindExtensions.SCENE, name=SceneTag.AUDIO),
        ]
        if quest_id := game_state.current_quest:
            tags.append(QuestIdTag(quest_id))

        task = music_gen.generate(
            text=prompt,
            append_output_to_file=True,
            streaming=True,
            output_file_id=context.chat_history.file.id,
            make_output_public=True,
            tags=tags,
        )
        task.wait()
        return task

    def request_camp_music_generation(self, context: AgentContext) -> Task:
        music_gen = context.client.use_plugin(self.PLUGIN_HANDLE)
        game_state = get_game_state(context)
        genre = game_state.genre or "Adventure"
        tone = game_state.tone or "Triumphant"

        prompt = f"background music for a quest game camp scene. {genre} genre. {tone}."

        tags = [
            Tag(kind=TagKindExtensions.STORY_CONTEXT, name=StoryContextTag.CAMP),
            Tag(kind=TagKindExtensions.CAMP, name=CampTag.AUDIO),
        ]
        if quest_id := game_state.current_quest:
            tags.append(QuestIdTag(quest_id))

        task = music_gen.generate(
            text=prompt,
            append_output_to_file=True,
            streaming=True,
            output_file_id=context.chat_history.file.id,
            make_output_public=True,
            tags=tags,
        )
        task.wait()
        return task
