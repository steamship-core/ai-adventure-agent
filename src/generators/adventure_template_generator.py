from abc import ABC, abstractmethod

from pydantic.main import BaseModel
from steamship import Block, PluginInstance
from steamship.agents.schema import AgentContext


class AdventureTemplateGenerator(BaseModel, ABC):
    """Generates an entire configuration -- multiple fields -- in a dict file."""

    @abstractmethod
    def suggest(
        self, variables: dict, generator: PluginInstance, context: AgentContext
    ) -> Block:
        pass
