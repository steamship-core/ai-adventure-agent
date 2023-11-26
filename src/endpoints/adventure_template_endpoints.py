import logging
from typing import Dict, List

from steamship import Block, Steamship, SteamshipError, Task
from steamship.agents.schema import AgentContext
from steamship.agents.service.agent_service import AgentService
from steamship.invocable import get, post
from steamship.invocable.package_mixin import PackageMixin
from steamship.utils.url import Verb

from generators.config_field_generators.editor_suggestion_generator import (
    EditorSuggestionGenerator,
)
from generators.image_generators import get_image_generator
from generators.utils import block_to_config_value, set_keypath_value
from schema.adventure_template import AdventureTemplate
from schema.objects import Item
from schema.server_settings import ServerSettings
from utils.context_utils import (
    get_adventure_template,
    get_server_settings,
    get_theme,
    save_adventure_template,
    save_server_settings,
)


class AdventureTemplateMixin(PackageMixin):
    """Provides endpoints for use creating an Adventure Template."""

    client: Steamship
    agent_service: AgentService

    def __init__(self, client: Steamship, agent_service: AgentService):
        self.client = client
        self.agent_service = agent_service

    def _update_server_settings(
        self, context: AgentContext, unsaved_server_settings: Dict = None
    ):
        """Saves over the server_settings object with any unsaved server-settings.

        This is OK because we're doing this to the development agent used by the editor - not an actual game agent.
        """
        if unsaved_server_settings is not None:
            logging.info(
                "Updating the server settings to generate the preview. This should only be done on the development agent."
            )
            try:
                server_settings = ServerSettings.parse_obj(unsaved_server_settings)
                existing_state = get_server_settings(context)
                existing_state.update_from_web(server_settings)
                save_server_settings(existing_state, context)
            except BaseException as e:
                logging.exception(e)
                raise e

    def _get_suggestion_variables(
        self, context: AgentContext, unsaved_server_settings: Dict = None
    ):
        """Builds the dictionary that we'll use to generate suggestions."""
        server_settings = get_server_settings(context)
        d = server_settings.dict()
        d.update(unsaved_server_settings or {})

        # Now also get the potential adventure_template dict, which is a SUPERSET including things like
        # characters, description, and tags. We don't save this on server_settings because we don't want to load
        # those things for every operation during gameplay.
        at = get_adventure_template(context)
        d.update(at or {})
        return d

    @post("/generate_preview")
    def generate_preview(
        self, field_name: str = None, unsaved_server_settings: Dict = None, **kwargs
    ) -> Block:
        context = self.agent_service.build_default_context()
        self._update_server_settings(context, unsaved_server_settings)

        server_settings = get_server_settings(context)

        if field_name == "item_image":
            theme = get_theme(server_settings.item_image_theme, context)
            generator = get_image_generator(theme)
            task = generator.request_item_image_generation(
                Item.editor_demo_object(), context
            )
        elif field_name == "camp_image":
            theme = get_theme(server_settings.camp_image_theme, context)
            generator = get_image_generator(theme)
            task = generator.request_camp_image_generation(context)
        elif field_name == "profile_image":
            theme = get_theme(server_settings.profile_image_theme, context)
            generator = get_image_generator(theme)
            task = generator.request_profile_image_generation(context)
        elif field_name == "scene_image":
            theme = get_theme(server_settings.quest_background_theme, context)
            generator = get_image_generator(theme)
            task = generator.request_scene_image_generation(
                "A magical enchanted forest.", context
            )
        else:
            raise SteamshipError(message=f"Unknown field name: {field_name}")

        if task and task.output and task.output.blocks:
            return task.output.blocks[0]

        raise SteamshipError(
            message=f"Unable to generate for {field_name} - no block on output."
        )

    @post("/generate_suggestion")
    def generate_suggestion(
        self,
        field_name: str = None,
        unsaved_server_settings: Dict = None,
        field_key_path: List = None,
        save_to_adventure_template: bool = False,
        **kwargs,
    ) -> Block:
        context = self.agent_service.build_default_context()
        self._update_server_settings(context, unsaved_server_settings)
        variables = self._get_suggestion_variables(context)
        generator = EditorSuggestionGenerator()

        # Make the suggestion
        field_key_path = field_key_path or []
        block = generator.generate_editor_suggestion(
            field_name, variables, field_key_path, context
        )

        # Maybe save it
        if save_to_adventure_template:
            value = block_to_config_value(block)
            adventure_template = get_adventure_template(context)
            adventure_template_dict = adventure_template.dict()
            set_keypath_value(adventure_template_dict, field_key_path, value)
            updated_adventure_template = AdventureTemplate.parse_obj(
                adventure_template_dict
            )
            save_adventure_template(updated_adventure_template, context)

        return block

    @post("/generate_configuration")
    def generate_configuration(
        self,
        field_key_paths: List = None,
        unsaved_server_settings: Dict = None,
        **kwargs,
    ) -> Task:
        context = self.agent_service.build_default_context()

        if field_key_paths is None:
            field_key_paths = [
                ["name"],
                ["short_description"],
                ["description"],
                ["adventure_goal"],
                ["adventure_background"],
                ["narrative_tone"],
                ["narrative_voice"],
                ["image"],
                ["tags", 0],
                ["tags", 1],
                ["tags", 2],
            ]

        # Apply them just for the first time.
        if unsaved_server_settings is not None:
            logging.info(
                "Updating the server settings to generate the suggestion. This should only be done on the development agent."
            )
            try:
                server_settings = ServerSettings.parse_obj(unsaved_server_settings)
                context = self.agent_service.build_default_context()
                existing_state = get_server_settings(context)
                existing_state.update_from_web(server_settings)
                save_server_settings(existing_state, context)
            except BaseException as e:
                logging.exception(e)
                raise e

        # Now we generate in sequence.
        last_task = None
        for field_key_path in field_key_paths:
            wait_on_tasks = []
            if last_task is not None:
                wait_on_tasks = [last_task]

            # Either something like `name` or `characters.name`
            if len(field_key_path) == 3:
                field_name = f"{field_key_path[0]}.{field_key_path[2]}"
            else:
                field_name = field_key_path[0]

            last_task = self.agent_service.invoke_later(
                method="/generate_suggestion",
                verb=Verb.POST,
                wait_on_tasks=wait_on_tasks,
                arguments={
                    "field_name": field_name,
                    "field_key_path": field_key_path,
                    "save_to_adventure_template": True,
                },
            )

        wait_on_tasks = []
        if last_task is not None:
            wait_on_tasks = [last_task]

        # Finally, we clear the generation_task_id value
        last_task = self.agent_service.invoke_later(
            method="/server_settings",
            verb=Verb.POST,
            wait_on_tasks=wait_on_tasks,
            arguments={"generation_task_id": ""},
        )

        server_settings = get_server_settings(context)
        server_settings.generation_task_id = last_task.task_id
        save_server_settings(server_settings, context)

        return last_task

    @post("/adventure_template")
    def post_adventure_template(self, **kwargs) -> dict:
        """Set the adventure_template."""
        try:
            adventure_template = AdventureTemplate.parse_obj(kwargs)
            context = self.agent_service.build_default_context()
            existing_adventure_template = get_adventure_template(context)
            existing_adventure_template.update_from_web(adventure_template)
            save_adventure_template(existing_adventure_template, context)
            return existing_adventure_template.dict()
        except BaseException as e:
            logging.exception(e)
            raise e

    @get("/adventure_template")
    def get_adventure_template(self) -> dict:
        """Get the adventure_template. This is a superset of server_settings."""
        context = self.agent_service.build_default_context()
        return get_adventure_template(context).dict()
