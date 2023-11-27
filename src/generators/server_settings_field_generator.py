"""A Config Generator is for the GAME CREATOR, not for the GAME PLAYER."""


from abc import ABC, abstractmethod

from pydantic.main import BaseModel
from steamship import Block, PluginInstance, SteamshipError, Task
from steamship.agents.schema import AgentContext


class ServerSettingsFieldGenerator(BaseModel, ABC):
    """Generates a single field in an Adventure Template."""

    @abstractmethod
    def inner_generate(
        self, variables: dict, generator: PluginInstance, context: AgentContext
    ) -> Block:
        pass

    def generate(
        self, variables: dict, generator: PluginInstance, context: AgentContext
    ) -> Block:
        return self.inner_generate(variables, generator, context)

    def task_to_str_block(self, task: Task) -> Block:
        task.wait()
        if task and task.output and task.output.blocks:
            block = task.output.blocks[0]
            # Make sure to await the full stream.
            block.text = block.raw().decode("utf-8")
            return block
        raise SteamshipError(message="Unable to fetch suggestion")
