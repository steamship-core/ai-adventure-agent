import logging
from typing import Dict, List

from steamship import Block, Steamship, SteamshipError, Task
from steamship.agents.schema import AgentContext
from steamship.agents.service.agent_service import AgentService
from steamship.invocable import get, post
from steamship.invocable.package_mixin import PackageMixin

from generators.adventure_template_generators.generate_all_generator import (
    GenerateAllGenerator,
)
from generators.editor_suggestion_generator import EditorSuggestionGenerator
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
        adventure_template = get_adventure_template(context)
        server_settings = get_server_settings(context)

        variables = {}

        # Now template it against the saved server settings
        variables.update(server_settings.dict())

        # Always update with adventure template second
        variables.update(adventure_template.dict())

        # Now update it with the unsaved server settings
        if unsaved_server_settings:
            variables.update(unsaved_server_settings)

        return variables

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

        try:
            variables = self._get_suggestion_variables(context)
        except BaseException as e:
            logging.exception(e)
            raise e

        generator = EditorSuggestionGenerator()
        logging.info(f"Generating {field_key_path} with variables {variables}")

        # Make the suggestion
        field_key_path = field_key_path or []
        try:
            block = generator.generate(field_name, variables, field_key_path, context)
        except BaseException as e:
            logging.exception(e)
            raise e

        # Maybe save it
        if save_to_adventure_template:
            value = block_to_config_value(block)
            adventure_template = get_adventure_template(context)
            adventure_template_dict = adventure_template.dict()
            try:
                set_keypath_value(adventure_template_dict, field_key_path, value)
            except BaseException as e:
                logging.error(e)
                raise e

            try:
                updated_adventure_template = AdventureTemplate.parse_obj(
                    adventure_template_dict
                )
            except BaseException as e:
                logging.error(e)
                raise e
            save_adventure_template(updated_adventure_template, context)

        return block

    @post("/generate_configuration")
    def generate_configuration(
        self,
        unsaved_server_settings: Dict = None,
        **kwargs,
    ) -> Task:
        context = self.agent_service.build_default_context()
        generator = GenerateAllGenerator()
        last_task = generator.generate(
            self.agent_service, context, unsaved_server_settings=unsaved_server_settings
        )
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
