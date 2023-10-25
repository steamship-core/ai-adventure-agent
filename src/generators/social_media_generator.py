from abc import ABC, abstractmethod

from pydantic.main import BaseModel
from steamship.agents.schema import AgentContext


class SocialMediaGenerator(BaseModel, ABC):
    @abstractmethod
    def generate_shareable_quest_snippet(
        self, quest_summary: str, context: AgentContext
    ) -> str:
        pass
