from abc import ABC, abstractmethod

from pydantic.main import BaseModel
from steamship import Task
from steamship.agents.schema import AgentContext

from schema.objects import Item
from schema.stable_diffusion_theme import (
    DEFAULT_THEME,
    PREMADE_THEMES,
    StableDiffusionTheme,
)
from utils.context_utils import get_server_settings


class ImageGenerator(BaseModel, ABC):
    def get_theme(self, name: str, context: AgentContext) -> StableDiffusionTheme:
        server_settings = get_server_settings(context)

        for theme in server_settings.image_themes or []:
            if name == theme.name:
                return theme
        for theme in PREMADE_THEMES:
            if name == theme.name:
                return theme
        return DEFAULT_THEME

    @abstractmethod
    def request_item_image_generation(self, item: Item, context: AgentContext) -> Task:
        pass

    @abstractmethod
    def request_profile_image_generation(self, context: AgentContext) -> Task:
        pass

    @abstractmethod
    def request_scene_image_generation(
        self, description: str, context: AgentContext
    ) -> Task:
        pass

    @abstractmethod
    def request_camp_image_generation(self, context: AgentContext) -> Task:
        pass
