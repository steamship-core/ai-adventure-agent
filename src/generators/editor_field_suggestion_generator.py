from abc import ABC, abstractmethod

from pydantic.main import BaseModel
from steamship import Block, PluginInstance, SteamshipError, Task
from steamship.agents.schema import AgentContext


class EditorFieldSuggestionGenerator(BaseModel, ABC):
    @abstractmethod
    def suggest(
        self, variables: dict, generator: PluginInstance, context: AgentContext
    ) -> Block:
        pass

    def task_to_str_block(self, task: Task) -> str:
        task.wait()
        if task and task.output and task.output.blocks:
            return task.output.blocks[0]
        raise SteamshipError(message="Unable to fetch suggestion")
