import abc
from abc import ABC

from steamship.agents.schema import Action, Agent, AgentContext

from utils.context_utils import FinishActionException


class InterruptiblePythonAgent(Agent, ABC):
    """Python implementers: implement your agent as a good old-fashioned Python script!

    Use context_utils.await_ask to simulate synchronously asking questions to the remote user!
    """

    PROMPT = ""

    @abc.abstractmethod
    def run(self, context: AgentContext):
        """Thing of this as the __main__ function of your agent.

        There's no concept of Action or Tool -- every time your agent receives a message, this method runs.
        """
        pass

    def next_action(self, context: AgentContext) -> Action:
        try:
            self.run(context)
        except FinishActionException as fae:
            # A FinishActionException indicates control-flow breakage, not error.
            # If we get one, return the action immediately.
            return fae.action
