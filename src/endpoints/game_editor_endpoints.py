import logging
from typing import Dict, List

from steamship import Block, MimeTypes, Steamship, SteamshipError, Task
from steamship.agents.service.agent_service import AgentService
from steamship.invocable import post
from steamship.invocable.package_mixin import PackageMixin
from steamship.utils.url import Verb

from generators.editor_suggestions.editor_suggestion_generator import (
    EditorSuggestionGenerator,
)
from generators.image_generators import get_image_generator
from schema.objects import Item
from schema.server_settings import ServerSettings
from utils.context_utils import get_server_settings, get_theme, save_server_settings


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
        save_result: bool = False,
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
            field_name, unsaved_server_settings or {}, field_key_path or [], context
        ):
            if save_result:
                # Save the result into the server_settings object.
                server_settings = None

                if len(field_key_path or []) == 1:
                    server_settings = get_server_settings(context)
                    if suggestion.mime_type == MimeTypes.TXT:
                        generated_text = suggestion.raw().decode("utf-8")
                        setattr(server_settings, field_name, generated_text)
                    else:
                        setattr(server_settings, field_name, suggestion.to_public_url())

                if server_settings is not None:
                    save_server_settings(server_settings, context)
            return suggestion

        raise SteamshipError(
            message=f"Unable to generate for {field_name} - no block on output."
        )

    @post("/generate_configuration")
    def generate_configuration(
        self,
        field_names: List = None,
        unsaved_server_settings: Dict = None,
        **kwargs,
    ) -> Task:
        if field_names is None:
            field_names = [
                "name",
                "short_description",
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
        for field_name in field_names:
            wait_on_tasks = []
            if last_task is not None:
                wait_on_tasks = [last_task]
            last_task = self.agent_service.invoke_later(
                method="/generate_suggestion",
                verb=Verb.POST,
                wait_on_tasks=wait_on_tasks,
                arguments={"field_name": field_name, "save_result": True},
            )

        return last_task
