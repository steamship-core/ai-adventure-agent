"""A Config Generator is for the GAME CREATOR, not for the GAME PLAYER."""


from abc import ABC, abstractmethod
from typing import Optional

from pydantic.main import BaseModel
from steamship import Block, PluginInstance, SteamshipError, Task
from steamship.agents.schema import AgentContext


class ServerSettingsFieldGenerator(BaseModel, ABC):
    """Generates a single field in an Adventure Template."""

    @abstractmethod
    def inner_generate(
        self,
        variables: dict,
        generator: PluginInstance,
        context: AgentContext,
        generation_config: Optional[dict] = None,
    ) -> Block:
        pass

    def generate(
        self,
        variables: dict,
        generator: PluginInstance,
        context: AgentContext,
        generation_config: Optional[dict] = None,
    ) -> Block:
        return self.inner_generate(variables, generator, context, generation_config)

    def task_to_str_block(self, task: Task) -> Block:
        task.wait()
        if task and task.output and task.output.blocks:
            block = task.output.blocks[0]
            # Make sure to await the full stream.
            try:
                block.text = block.raw().decode("utf-8")
                return block
            except BaseException as ex:
                raise SteamshipError(
                    message="Unable to generate content. This is often a result of the content moderation throwing a warning.",
                    error=ex,
                )
        raise SteamshipError(message="Unable to fetch suggestion")
