from typing import Final

from steamship import Tag, Task
from steamship.agents.schema import AgentContext

from generators.music_generator import MusicGenerator
from generators.utils import safe_format
from utils.context_utils import get_game_state, get_server_settings
from utils.tags import CampTag, QuestIdTag, SceneTag, StoryContextTag, TagKindExtensions


class MetaMusicGenerator(MusicGenerator):
    PLUGIN_HANDLE: Final[str] = "music-generator"

    def request_scene_music_generation(
        self, description: str, context: AgentContext
    ) -> Task:
        game_state = get_game_state(context)
        server_settings = get_server_settings(context)
        music_gen = context.client.use_plugin(
            self.PLUGIN_HANDLE, config={"duration": server_settings.music_duration}
        )

        prompt = safe_format(
            server_settings.scene_music_generation_prompt,
            {
                "tone": server_settings.narrative_tone,
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
        game_state = get_game_state(context)
        server_settings = get_server_settings(context)
        music_gen = context.client.use_plugin(
            self.PLUGIN_HANDLE, config={"duration": server_settings.music_duration}
        )

        prompt = safe_format(
            server_settings.camp_music_generation_prompt,
            {
                "tone": server_settings.narrative_tone,
            },
        )

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
