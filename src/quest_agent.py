from steamship import MimeTypes
from steamship.agents.schema import Action, Agent, AgentContext
from steamship.agents.schema.action import FinishAction
from steamship.data import Block

from script import Script


class QuestAgent(Agent):
    """
    DESIGN GOALS:
    This implements the "going on a quest" and only that.
    It can be slotted into as a state machine sub-agent by the overall agent.
    """

    PROMPT = ""

    def conclude_quest(self, context: AgentContext) -> Action:
        """
        Block is of type END SCENE and contains JSON with the summary.

        - how much gold
        - what items
        - summary of the journey

        Every Quest is a different chat history.
        - There would be a quest log button somewhere.
        - In that quest log.
        """
        script = Script(context.chat_history)

        script.append_assistant_message(
            text="The quest is over.", mime_type=MimeTypes.MKD
        )

        return FinishAction(
            output=[Block(text="The quest is over.", mime_type=MimeTypes.MKD)]
        )

    def next_action(self, context: AgentContext) -> Action:
        script = Script(context.chat_history)

        script.append_assistant_message(
            text="Now we're going to go on a quest", mime_type=MimeTypes.MKD
        )

        script.append_assistant_message(text="<audio>", mime_type=MimeTypes.MKD)

        script.append_assistant_message(text="<img>", mime_type=MimeTypes.MKD)

        script.append_assistant_message(
            text="A problem occurs!", mime_type=MimeTypes.MKD
        )

        script.append_assistant_message(
            text="How do you want to handle it?", mime_type=MimeTypes.MKD
        )

        script.append_assistant_message(
            text="You've handled it!", mime_type=MimeTypes.MKD
        )

        script.append_assistant_message(
            text="Here's the summary of the quest {}", mime_type=MimeTypes.MKD
        )

        return self.conclude_quest(context)
