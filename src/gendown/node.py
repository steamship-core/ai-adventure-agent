import logging
from enum import Enum
from typing import List, Optional
from marko import Markdown
from marko.block import BlankLine, Heading, Paragraph, CodeBlock
from marko.element import Element
from marko.md_renderer import MarkdownRenderer
import re
from pydantic import BaseModel, Field
from steamship import SteamshipError
from steamship.agents.logging import AgentLogging
from steamship.agents.schema import AgentContext
from steamship.utils.kv_store import KeyValueStore

from utils.context_utils import await_ask
from utils.generation_utils import send_story_generation


def get_prompt_vars(prompt: str) -> List[str]:
    """Fetches the list of {words} inside curly braces."""
    return re.findall("{([^}]+)", prompt)


def validate_prompt_args(prompt: str, valid_args: List[str]):
    """Validates that the prompt doesn't contain an argumnt that isn't in the list."""
    prompt_vars = get_prompt_vars(prompt)
    for var_name in prompt_vars:
        if var_name not in valid_args:
            raise SteamshipError(
                message=f"This prompt uses a variable ({var_name}) that is not in the list of valid variables ({valid_args}). The full prompt was [{prompt}]. Please remove this variable and try again."
            )

def safe_format(text: str, params: dict) -> str:
    """Safely formats a user-provided string by replacing {key} with `value` for all (key,value) pairs in `params`."""
    ret = text
    for (key, value) in params.items():
        ret = ret.replace("{" + key + "}", value)

    return ret


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

    def append_child(self, node: "Node"):
        if self.children is None:
            self.children = []

        node.id = f"{self.id}.{len(self.children)}"
        self.children.append(node)

    def visit(self, context: AgentContext, kv: KeyValueStore):
        if not self.should_run(context, kv):
            logging.info(f"[Visit {self.id}] - Skip!",
            extra = {
                        AgentLogging.IS_MESSAGE: True,
                        AgentLogging.MESSAGE_TYPE: AgentLogging.THOUGHT,
                        AgentLogging.MESSAGE_AUTHOR: AgentLogging.AGENT,
                    },
            )
            return

        logging.info(f"[Visit {self.id}] - Run",
            extra = {
                        AgentLogging.IS_MESSAGE: True,
                        AgentLogging.MESSAGE_TYPE: AgentLogging.THOUGHT,
                        AgentLogging.MESSAGE_AUTHOR: AgentLogging.AGENT,
                    },
        )

        for child in self.children or []:
            child.visit(context, kv)

        # Now run us.

        if self.kind == Kind.output:
            self.run_output_command(context, kv)
        elif self.kind == Kind.command and self.command == "Input":
            self.run_input_command(context, kv)
        elif self.kind == Kind.command and self.command == "GenerateText":
            self.run_generate_text_command(context, kv)
        elif self.kind == Kind.command and self.command == "GenerateImage":
            self.run_generate_image_command(context, kv)

        # Cache that we ran.
        kv.set(f"_ran{self.id}", {"value": True})

    def should_run(self, context: AgentContext, kv: KeyValueStore):
        if self.kind == Kind.scope or not not self.kind:
            return True

        return (kv.get(f"_ran{self.id}") or {}).get("value", False) == False

    def template(self, text: str, kv: KeyValueStore):
        """Templates the string against our KV store"""
        inline_vars = get_prompt_vars(text)
        if not inline_vars:
            return text
        # Not efficient
        d = {}
        for var in inline_vars:
            # Defaults to empty string; bad. Just hashing the prototype out
            d[var] = (kv.get(var) or {}).get("value", "")

        return safe_format(text, d)

    def run_output_command(self, context: AgentContext, kv: KeyValueStore):
        logging.info(f"[Gendown Command: Output]",
            extra = {
                        AgentLogging.IS_MESSAGE: True,
                        AgentLogging.MESSAGE_TYPE: AgentLogging.THOUGHT,
                        AgentLogging.MESSAGE_AUTHOR: AgentLogging.AGENT,
                    },
        )

        message = self.template(self.text, kv)
        print(f"[Assistant] {message}")
        context.chat_history.append_assistant_message(
            text=message
        )

    def run_generate_text_command(self, context: AgentContext, kv: KeyValueStore):
        logging.info(f"[Gendown Command: Generate Text]",
            extra = {
                        AgentLogging.IS_MESSAGE: True,
                        AgentLogging.MESSAGE_TYPE: AgentLogging.THOUGHT,
                        AgentLogging.MESSAGE_AUTHOR: AgentLogging.AGENT,
                    },
        )

        if self.inline_command_arg is None:
            # We're generating it to the chat history!
            message = self.template(self.text, kv)
            print(f"[Assistant] {message}")
            send_story_generation(message, context=context)
        else:
            # We're generating it into a variable!
            return

    def run_generate_image_command(self, context: AgentContext, kv: KeyValueStore):
        logging.info(f"[Gendown Command: Generate Image]",
            extra = {
                        AgentLogging.IS_MESSAGE: True,
                        AgentLogging.MESSAGE_TYPE: AgentLogging.THOUGHT,
                        AgentLogging.MESSAGE_AUTHOR: AgentLogging.AGENT,
                    },
        )

        if self.inline_command_arg is None:
            # We're generating it to the chat history!
            message = self.template(self.text, kv)
            print(f"[Assistant] {message}")
            send_story_generation(message, context=context)
        else:
            # We're generating it into a variable!
            return

    def run_input_command(self, context: AgentContext, kv: KeyValueStore):
        logging.info(f"[Gendown Command: Input]",
            extra = {
                        AgentLogging.IS_MESSAGE: True,
                        AgentLogging.MESSAGE_TYPE: AgentLogging.THOUGHT,
                        AgentLogging.MESSAGE_AUTHOR: AgentLogging.AGENT,
                    },
        )

        # TODO the await ask shouldn't actually say something new here; would need a slightly modded version.
        val = await_ask("?", context, key_suffix=self.inline_command_arg)
        kv.set(self.inline_command_arg, {"value": val})
