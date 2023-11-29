import logging
from typing import Dict, List

from steamship import Block, Steamship, SteamshipError, Task
from steamship.agents.schema import AgentContext
from steamship.invocable import get, post
from steamship.invocable.package_mixin import PackageMixin

from generators.editor_suggestion_generator import EditorSuggestionGenerator
from generators.image_generators import get_image_generator
from generators.server_settings_generators.generate_all_generator import (
    GenerateAllGenerator,
)
from generators.server_settings_generators.generate_using_title_and_description_generator import (
    GenerateUsingTitleAndDescriptionGenerator,
)
from generators.utils import block_to_config_value, set_keypath_value
from schema.objects import Item
from schema.server_settings import ServerSettings
from schema.server_settings_schema import SCHEMA
from utils.agent_service import AgentService
from utils.context_utils import get_server_settings, get_theme, save_server_settings


class ServerSettingsMixin(PackageMixin):
    """Provides endpoints for Game State."""

    agent_service: AgentService
    client: Steamship

    def __init__(self, client: Steamship, agent_service: AgentService):
        self.client = client
        self.agent_service = agent_service

    @get("/server_settings_schema")
    def get_server_settings_schema(self) -> dict:
        return SCHEMA

    @post("/server_settings")
    def post_server_settings(self, **kwargs) -> dict:
        """Set the server settings."""
        try:
            server_settings = ServerSettings.parse_obj(kwargs)
            context = self.agent_service.build_default_context()
            existing_state = get_server_settings(context)
            existing_state.update_from_web(server_settings)
            save_server_settings(existing_state, context)
            return server_settings.dict()
        except BaseException as e:
            logging.exception(e)
            raise e

    @post("/patch_server_settings")
    def patch_server_settings(self, **kwargs) -> dict:
        """Set the server settings -- only applying updates contained in kwargs."""
        try:
            context = self.agent_service.build_default_context()
            server_settings = get_server_settings(context)
            for k, v in kwargs.items():
                setattr(server_settings, k, v)
            save_server_settings(server_settings, context)
            return server_settings.dict()
        except BaseException as e:
            logging.exception(e)
            raise e

    @get("/server_settings")
    def get_server_settings(self) -> dict:
        """Get the server settings."""
        context = self.agent_service.build_default_context()
        return get_server_settings(context).dict()

    @post("/generate_configuration")
    def generate_configuration(
        self,
        unsaved_server_settings: Dict = None,
        generation_config: Dict = None,
        **kwargs,
    ) -> Task:
        context = self.agent_service.build_default_context()

        logging.info(
            f"/generate_configuration with unsaved_server_settings = {unsaved_server_settings}"
        )
        if unsaved_server_settings and "source_story_text" in unsaved_server_settings:
            logging.info("Generating from a story because `source_story_text`.")
            generator = GenerateUsingTitleAndDescriptionGenerator()
        else:
            logging.info("Generating scratch since no `source_story_text`.")
            generator = GenerateAllGenerator()

        last_task = generator.generate(
            self.agent_service,
            context,
            unsaved_server_settings=unsaved_server_settings,
            generation_config=generation_config,
        )
        return last_task

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

        variables = {}

        # Now template it against the saved server settings
        variables.update(server_settings.dict())

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
        save_to_server_settings: bool = False,
        generation_config: Dict = None,
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
            block = generator.generate(
                field_name,
                variables,
                field_key_path,
                context,
                generation_config=generation_config,
            )
        except BaseException as e:
            logging.exception(e)
            raise e

        # Maybe save it
        if save_to_server_settings:
            value = block_to_config_value(block)
            server_settings = get_server_settings(context)
            server_settings_dict = server_settings.dict()
            try:
                set_keypath_value(server_settings_dict, field_key_path, value)
            except BaseException as e:
                logging.error(e)
                raise e

            try:
                updated_server_settings = ServerSettings.parse_obj(server_settings_dict)
                save_server_settings(updated_server_settings, context)
            except BaseException as e:
                logging.error(e)
                raise e

        return block
