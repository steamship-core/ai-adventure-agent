from abc import ABC, abstractmethod

from pydantic.main import BaseModel
from steamship import Task
from steamship.agents.schema import AgentContext

from schema.objects import Item


class ImageGenerator(BaseModel, ABC):
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

    @abstractmethod
    def request_adventure_image_generation(self, context: AgentContext) -> Task:
        pass
