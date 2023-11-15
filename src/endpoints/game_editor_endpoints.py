from typing import Dict

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


class GameEditorMixin(PackageMixin):
    """Provides endpoints for use within the game editor."""

    client: Steamship
    agent_service: AgentService

    def __init__(self, client: Steamship, agent_service: AgentService):
        self.client = client
        self.agent_service = agent_service

    @post("/generate_preview")
    def generate_preview(self, field_name: str = None, **kwargs) -> Block:
        context = self.agent_service.build_default_context()
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
        self, field_name: str = None, unsaved_server_settings: Dict = None, **kwargs
    ) -> Block:
        context = self.agent_service.build_default_context()
        generator = EditorSuggestionGenerator()
        task = generator.generate_editor_suggestion(
            field_name, unsaved_server_settings or {}, context
        )

        if task and task.output and task.output.blocks:
            return task.output.blocks[0]

        raise SteamshipError(
            message=f"Unable to generate for {field_name} - no block on output."
        )
