from typing import Dict

from steamship import Steamship
from steamship.agents.service.agent_service import AgentService
from steamship.invocable import post
from steamship.invocable.package_mixin import PackageMixin

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

    @post("/generate_preview_item_image")
    def generate_preview_item_image(self, item: Dict = None, **kwargs) -> dict:
        context = self.agent_service.build_default_context()
        image_generator = StableDiffusionWithLorasImageGenerator()
        _item = Item.editor_demo_object(item)
        return image_generator.request_item_image_generation(_item, context)

    @post("/generate_preview_camp_image")
    def generate_preview_camp_image(self, **kwargs) -> dict:
        context = self.agent_service.build_default_context()
        image_generator = StableDiffusionWithLorasImageGenerator()
        return image_generator.request_camp_image_generation(context)

    @post("/generate_preview_profile_image")
    def generate_preview_profile_image(self, **kwargs) -> dict:
        context = self.agent_service.build_default_context()
        image_generator = StableDiffusionWithLorasImageGenerator()
        return image_generator.request_profile_image_generation(context)

    @post("/generate_preview_scene_image")
    def generate_preview_scene_image(self, description: str = None, **kwargs) -> dict:
        context = self.agent_service.build_default_context()
        image_generator = StableDiffusionWithLorasImageGenerator()
        return image_generator.request_scene_image_generation(
            description or "A magical enchanged forest.", context
        )
