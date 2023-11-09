from typing import List

from steamship import Block
from steamship.agents.schema import Action, Agent, AgentContext, FinishAction
from steamship.agents.schema.message_selectors import MessageWindowMessageSelector

from tools.start_quest_tool import StartQuestTool
from utils.moderation_utils import is_block_excluded


class NonExcludedMessageWindowSelector(MessageWindowMessageSelector):
    def get_messages(self, messages: List[Block]) -> List[Block]:
        # choice here: if the user has been submitting a bunch of problematic conversation
        #              then we are ok "forgetting" the distant context. so, we can trim from
        #              the discovered window, rather than first filtering and then selecting
        #              via the window.
        context_messages = super().get_messages(messages)
        return [msg for msg in context_messages if not is_block_excluded(msg)]


class CampAgent(Agent):
    """The Camp Agent is currently just
    the
    """

    def __init__(self, **kwargs):
        super().__init__(
            tools=[StartQuestTool()],  # , StartConversationTool()],
            **kwargs,
        )

    def next_action(self, context: AgentContext) -> Action:
        """Only one action possible - start quest (for CLI usage).  Else return dummy string."""

        last_message = ""
        if last_message_block := context.chat_history.last_user_message:
            if last_message_block.text is not None:
                last_message = last_message_block.text

        if last_message.lower() == "quest":
            return Action(tool=self.tools[0].name, output=[], input=[])
        else:
            return FinishAction(
                output=[Block(text=f"Camp agent received text: {last_message}")]
            )
