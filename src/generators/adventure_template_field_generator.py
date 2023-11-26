"""A Config Generator is for the GAME CREATOR, not for the GAME PLAYER."""


from abc import ABC, abstractmethod

from pydantic.main import BaseModel
from steamship import Block, PluginInstance
from steamship.agents.schema import AgentContext


class AdventureTemplateFieldGenerator(BaseModel, ABC):
    """Generates a single field in an Adventure Template."""

    @abstractmethod
    def suggest(
        self, variables: dict, generator: PluginInstance, context: AgentContext
    ) -> Block:
        pass
