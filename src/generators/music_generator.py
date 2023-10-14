from abc import ABC, abstractmethod

from pydantic.main import BaseModel
from steamship import Task
from steamship.agents.schema import AgentContext


class MusicGenerator(BaseModel, ABC):

    @abstractmethod
    def request_scene_music_generation(
        self, description: str, context: AgentContext
    ) -> Task:
        pass
