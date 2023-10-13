from steamship.agents.schema import Action, AgentContext
from steamship.agents.schema.action import FinishAction

from tools.end_quest_tool import EndQuestTool
from utils.generation_utils import send_story_generation
from utils.interruptible_python_agent import InterruptiblePythonAgent


class DiagnosticAgent(InterruptiblePythonAgent):
    """
    The agent is used to test streaming.
    """

    test_name: str = "knock-knock"

    def __init__(self, test_name: str, **kwargs):
        super().__init__(**kwargs)
        self.test_name = test_name

    def run(self, context: AgentContext) -> Action:
        """
        It could go in a tool, but that doesn't feel necessary.. there are some other spots where tools feel very
        well fit, but this might be better left open-ended so we can stop/start things as we like.
        """
        send_story_generation(
            "Tell a knock knock joke",
            quest_name="Knock Knock",
            context=context,
        )
        blocks = EndQuestTool().run([], context)
        return FinishAction(output=blocks)
