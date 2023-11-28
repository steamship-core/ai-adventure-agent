from steamship import Block
from steamship.agents.schema import Action, AgentContext
from steamship.agents.schema.action import FinishAction

from utils.context_utils import emit
from utils.interruptible_python_agent import InterruptiblePythonAgent


class GeneratingAgent(InterruptiblePythonAgent):
    def __init__(self, **kwargs):
        super().__init__(tools=[], **kwargs)

    def run(self, context: AgentContext) -> Action:
        blocks = [
            Block(text="The game is currently generating it's configuration.", tags=[])
        ]
        emit(blocks, context)
        return FinishAction(output=blocks)
