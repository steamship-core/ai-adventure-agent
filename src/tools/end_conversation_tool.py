import logging
from typing import Any, List, Union

from steamship import Block, Task
from steamship.agents.logging import AgentLogging
from steamship.agents.schema import AgentContext, Tool

from context_utils import get_user_settings, save_user_settings
from schema.user_settings import UserSettings


class EndConversationTool(Tool):
    """Ends a conversation with an NPC.

    This Tool is meant to TRANSITION the user state out of "in_dialogue" by modifying user_settings and returning.

    It can either be called by:
     - The NPC AGENT (when in full-chat mode) -- see npc_agent.py
     - The WEB APP (when in web-mode, via api) -- see npc_mixin.py
    """

    def __init__(self, **kwargs):
        kwargs["name"] = "EndConversationTool"
        kwargs[
            "agent_description"
        ] = "Use to exit a converation. Use this tool if they say they want to end the conversation, or go back to camp, or go on a quest."
        kwargs[
            "human_description"
        ] = "Tool to leave a conversation. Modifies the global state such that the in_conversation_with bit is set to None."
        # It always returns.. OK! Let's go!
        kwargs["is_final"] = True
        super().__init__(**kwargs)

    def log_error(self, msg: str):
        logging.error(
            msg,
            extra={
                AgentLogging.IS_MESSAGE: True,
                AgentLogging.MESSAGE_TYPE: AgentLogging.THOUGHT,
                AgentLogging.MESSAGE_AUTHOR: AgentLogging.TOOL,
                AgentLogging.TOOL_NAME: self.name,
            },
        )
        return msg

    def end_conversation(
        self,
        user_settings: UserSettings,
        context: AgentContext,
    ) -> str:
        if not user_settings.in_conversation_with:
            return self.log_error(
                "You weren't currently in a conversation with anyone.",
            )

        npc = user_settings.in_conversation_with

        # Finally.. we have our NPC.
        user_settings.in_conversation_with = None
        save_user_settings(user_settings, context)

        return f"You've left the conversation with {npc} and returned to camp."

    def run(
        self, tool_input: List[Block], context: AgentContext
    ) -> Union[List[Block], Task[Any]]:
        user_settings = get_user_settings(context)
        msg = self.end_conversation(user_settings, context)
        return [Block(text=msg)]
