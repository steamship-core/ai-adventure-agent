from enum import Enum
from typing import List, Optional
from marko import Markdown
from marko.block import BlankLine, Heading, Paragraph, CodeBlock
from marko.element import Element
from marko.md_renderer import MarkdownRenderer
import re
from pydantic import BaseModel, Field
from steamship.agents.schema import AgentContext
from steamship.utils.kv_store import KeyValueStore

from utils.context_utils import await_ask


class Kind(str, Enum):
    scope = "scope"
    output = "output"
    command = "command"

class Node(BaseModel):
    """An AST Node in a Gendown Program."""

    id: Optional[str] = Field("", description="Id. Used for resume!")
    text: Optional[str] = Field("", description="The content")
    kind: Optional[str] = Field("", description="")
    command: Optional[str] = Field("", description="The comamnd, if kind is command")
    inline_command_arg: Optional[str] = Field("")
    children: Optional[List["Node"]]

    dataframe = {}

    def visit(self, context: AgentContext, kv: KeyValueStore):
        if self.kind == Kind.output:
            self.run_output_command(context)
        elif self.kind == Kind.command and self.command == "Input":
            self.run_input_command(context)


    def run_output_command(self, context: AgentContext, kv: KeyValueStore):
        val = self.context[self.inline_command_arg] = await_ask("?", context, key_suffix=self.inline_command_arg)
        # for keys in
        context.chat_history.append_assistant_message(
            text=self.text,
        )

        kv.set(self.inline_command_arg, {"value": val})

    def run_input_command(self, context: AgentContext, kv: KeyValueStore):
        val = self.context[self.inline_command_arg] = await_ask("?", context, key_suffix=self.inline_command_arg)
        kv.set(self.inline_command_arg, {"value": val})
