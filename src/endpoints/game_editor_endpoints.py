import logging
from typing import Dict, List

from steamship import Block, Steamship, SteamshipError
from steamship.agents.service.agent_service import AgentService
from steamship.invocable import post
from steamship.invocable.package_mixin import PackageMixin

from generators.editor_suggestions.editor_suggestion_generator import (
    EditorSuggestionGenerator,
)
from generators.image_generators.stable_diffusion_with_loras import (
    StableDiffusionWithLorasImageGenerator,
)
from schema.objects import Item
from schema.server_settings import ServerSettings
from utils.context_utils import get_server_settings, save_server_settings


class GameEditorMixin(PackageMixin):
    """Provides endpoints for use within the game editor."""

    client: Steamship
    agent_service: AgentService

    def __init__(self, client: Steamship, agent_service: AgentService):
        self.client = client
        self.agent_service = agent_service

    @post("/generate_preview")
    def generate_preview(
        self, field_name: str = None, unsaved_server_settings: Dict = None, **kwargs
    ) -> Block:
        context = self.agent_service.build_default_context()

        if unsaved_server_settings is not None:
            logging.info(
                "Updating the server settings to generate the preview. This should only be done on the development agent."
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

        image_generator = StableDiffusionWithLorasImageGenerator()

        if field_name == "item_image":
            task = image_generator.request_item_image_generation(
                Item.editor_demo_object(), context
            )
        elif field_name == "camp_image":
            task = image_generator.request_camp_image_generation(context)
        elif field_name == "profile_image":
            task = image_generator.request_profile_image_generation(context)
        elif field_name == "scene_image":
            task = image_generator.request_scene_image_generation(
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
        **kwargs,
    ) -> Block:
        context = self.agent_service.build_default_context()

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

        generator = EditorSuggestionGenerator()
        if suggestion := generator.generate_editor_suggestion(
            field_name, unsaved_server_settings or {}, field_key_path, context
        ):
            return suggestion

        raise SteamshipError(
            message=f"Unable to generate for {field_name} - no block on output."
        )
