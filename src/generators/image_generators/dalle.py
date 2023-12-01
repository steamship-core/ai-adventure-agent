from typing import Final, List

from steamship import SteamshipError, Tag, Task
from steamship.agents.schema import AgentContext
from steamship.data import TagValueKey

from generators.image_generator import ImageGenerator
from schema.image_theme import DalleTheme
from schema.objects import Item
from utils.context_utils import get_game_state, get_server_settings, get_theme
from utils.tags import (
    CampTag,
    CharacterTag,
    ItemTag,
    QuestIdTag,
    SceneTag,
    StoryContextTag,
    TagKindExtensions,
)


class DalleImageGenerator(ImageGenerator):
    PLUGIN_HANDLE: Final[str] = "dall-e"

    def get_theme(self, theme_name: str, context) -> DalleTheme:
        theme = get_theme(theme_name, context)
        if not theme.is_dalle:
            raise SteamshipError(
                f"Theme {theme_name} is not DALL-E but this is the DALL-E Generator"
            )
        d = theme.dict()
        return DalleTheme.parse_obj(d)

    def generate(
        self,
        context,
        theme_name: str,
        prompt: str,
        template_vars: dict,
        image_size: str,
        tags: List[Tag],
    ) -> Task:
        theme = self.get_theme(theme_name, context)
        prompt = theme.make_prompt(prompt, template_vars)

        options = {
            "style": theme.style,
        }

        # Fixes for DALL-E 2 which only supports squares.
        # TODO: Find a way to talk about image sizes that works across models. Maybe just have three options: default, portrait, landscape?
        if theme.model == "dall-e-2":
            image_size = "1024x1024"

        # TODO(doug): cache plugin instance by client workspace
        dalle = context.client.use_plugin(
            DalleImageGenerator.PLUGIN_HANDLE,
            config={
                "model": theme.model,
                "size": image_size,
                "quality": theme.quality,
            },
        )

        return dalle.generate(
            text=prompt,
            tags=tags,
            streaming=True,
            append_output_to_file=True,
            output_file_id=context.chat_history.file.id,
            make_output_public=True,
            options=options,
        )

    def request_item_image_generation(self, item: Item, context: AgentContext) -> Task:
        game_state = get_game_state(context)
        server_settings = get_server_settings(context)
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

        task = self.generate(
            context=context,
            theme_name=server_settings.item_image_theme,
            prompt=server_settings.item_image_prompt,
            template_vars={
                "tone": server_settings.narrative_tone,
                "name": item.name,
                "description": item.description,
            },
            image_size="1024x1024",
            tags=tags,
        )

        task.wait()
        return task

    def request_profile_image_generation(self, context: AgentContext) -> Task:
        game_state = get_game_state(context)
        server_settings = get_server_settings(context)

        name = game_state.player.name
        description = game_state.player.description

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

        task = self.generate(
            context=context,
            theme_name=server_settings.profile_image_theme,
            prompt=server_settings.profile_image_prompt,
            template_vars={
                "name": name,
                "tone": server_settings.narrative_tone,
                "genre": server_settings.narrative_voice,
                "description": description,
            },
            image_size="1024x1792",
            tags=tags,
        )

        task.wait()
        return task

    def request_character_image_generation(
        self, name: str, description: str, context: AgentContext
    ) -> Task:
        server_settings = get_server_settings(context)
        task = self.generate(
            context=context,
            theme_name=server_settings.profile_image_theme,
            prompt=server_settings.profile_image_prompt,
            template_vars={
                "name": name,
                "tone": server_settings.narrative_tone,
                "genre": server_settings.narrative_voice,
                "description": description,
            },
            image_size="1024x1792",
            tags=[],  # no tags, as this is strictly for in-editor usage.
        )

        task.wait()
        return task

    def request_scene_image_generation(
        self, description: str, context: AgentContext
    ) -> Task:
        game_state = get_game_state(context)
        server_settings = get_server_settings(context)

        tags = [
            Tag(kind=TagKindExtensions.SCENE, name=SceneTag.BACKGROUND),
        ]
        if quest_id := game_state.current_quest:
            tags.append(QuestIdTag(quest_id))

        task = self.generate(
            context=context,
            theme_name=server_settings.quest_background_theme,
            prompt=server_settings.quest_background_image_prompt,
            template_vars={
                "tone": server_settings.narrative_tone,
                "genre": server_settings.narrative_voice,
                "description": description,
            },
            image_size="1792x1024",
            tags=tags,
        )

        task.wait()
        return task

    def request_camp_image_generation(self, context: AgentContext) -> Task:
        server_settings = get_server_settings(context)

        tags = [
            Tag(kind=TagKindExtensions.STORY_CONTEXT, name=StoryContextTag.CAMP),
            Tag(kind=TagKindExtensions.CAMP, name=CampTag.IMAGE),
        ]

        task = self.generate(
            context=context,
            theme_name=server_settings.camp_image_theme,
            prompt=server_settings.camp_image_prompt,
            template_vars={
                "tone": server_settings.narrative_tone,
                "genre": server_settings.narrative_voice,
            },
            image_size="1792x1024",
            tags=tags,
        )
        task.wait()
        return task

    def request_adventure_image_generation(self, context: AgentContext) -> Task:
        server_settings = get_server_settings(context)

        tags = []

        task = self.generate(
            context=context,
            theme_name=server_settings.adventure_image_theme,
            prompt="Cinematic, 8k, movie advertising image, {narrative_voice}, Movie Title: {name}",
            template_vars={
                "narrative_voice": server_settings.narrative_voice,
                "name": server_settings.name,
                "tone": server_settings.narrative_tone,
                "genre": server_settings.narrative_voice,
            },
            image_size="1024x1792",
            tags=tags,
        )
        task.wait()
        return task
