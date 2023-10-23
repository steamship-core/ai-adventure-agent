import logging
from typing import List, Optional

from steamship import Block, MimeTypes, Tag
from steamship.agents.logging import AgentLogging
from steamship.agents.schema import Action, AgentContext, Tool
from steamship.agents.schema.action import FinishAction
from steamship.utils.kv_store import KeyValueStore

from gendown.node import Node
from gendown.parser import parse_gendown
from utils.interruptible_python_agent import InterruptiblePythonAgent


class GendownAgent(InterruptiblePythonAgent):
    """Implements the flow to onboared a new player.

    - For pure chat users, this is essential.
    - For web users, this is not necessary, as the website will provide this information via API.

    This flow uses checks against the game_state object to fast-forward through this logic in such that only
    the missing pieces of information are asked of the user in either chat or web mode.
    """
    class Config:
        arbitrary_types_allowed = True

    gendown: str
    kv: Optional[KeyValueStore]
    node: Optional[Node]

    def __init__(self, gendown: str = None, kv: KeyValueStore = None, **kwargs):
        super().__init__(tools=[], gendown=gendown, **kwargs)
        logging.debug("Parsing Gendown AST",
        extra = {
                    AgentLogging.IS_MESSAGE: True,
                    AgentLogging.MESSAGE_TYPE: AgentLogging.THOUGHT,
                    AgentLogging.MESSAGE_AUTHOR: AgentLogging.AGENT,
                },
        )
        self.kv = kv
        self.node = parse_gendown(self.gendown)

    def run(self, context: AgentContext) -> Action:  # noqa: C901
        self.node.visit(context, self.kv)
        return FinishAction(output=[Block(text="Gendown has Completed")])
