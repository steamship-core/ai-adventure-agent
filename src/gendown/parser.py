from enum import Enum
from typing import List, Optional
from marko import Markdown
from marko.block import BlankLine, Heading, Paragraph, CodeBlock
from marko.element import Element
from marko.md_renderer import MarkdownRenderer
import re
from pydantic import BaseModel, Field
from steamship import SteamshipError
from steamship.agents.schema import AgentContext

from gendown.node import Kind, Node


def is_output(node: Element):
    """By default, every markdown element is assumed output."""
    return True

def is_command(node: Element):
    """An element is a command if:

    It is a Paragraph that begins with [BracketedText]
    """
    if isinstance(node, Paragraph) or isinstance(node, CodeBlock):
        if node.children and isinstance(node.children[0].children, str):
            children = node.children
            content = children[0].children
            if m := re.match(r"^\[(.*)](.*)$", content, re.MULTILINE | re.DOTALL):
                command = m.groups()[0]
                command_parts = command.split(" ")
                default_argument = m.groups()[1]

                if isinstance(node, Paragraph):
                    # We need to render the rest of the children in!
                    # This would be, for example, the other lines of text in a paragraph.
                    # Or sub nodes of this node!
                    for child in children[1:]:
                        renderer = MarkdownRenderer()
                        renderer.__enter__()
                        default_argument += renderer.render(child)

                return Node(
                    kind=Kind.command,
                    command=command_parts[0].strip(),
                    inline_command_arg=" ".join(command_parts[1:]).strip(),
                    text=default_argument.strip()
                )
    return None


def parse_gendown(text: str) -> Node:
    markdown = Markdown(extensions=[])

    md = markdown.parse(text)

    root = Node(id="0", kind=Kind.scope, children=[])

    cursor = Node(kind=Kind.output)

    def reduce():
        nonlocal root
        nonlocal cursor
        if cursor.text:
            cursor.text = cursor.text.strip()
            root.append_child(cursor)
        cursor = Node(kind=Kind.output)

    renderer = MarkdownRenderer()
    renderer.__enter__()

    for child in md.children:
        if cmd := is_command(child):
            reduce()
            root.append_child(cmd)
        elif is_output(child):
            cursor.text += renderer.render(child)
    reduce()

    return root



if __name__ == "__main__":
    # client = Steamship(workspace="thing-crater-i8mli")
    # repl = AgentREPL(
    #     cast(AgentService, AiScriptMain), agent_package_config={}, client=client
    # )
    # repl.run(dump_history_on_exit=True)

    parse_gendown("""
# Asking Questions

Before we go further, let's get to know each other!

I'm the Gendown guide.

What's your name?

[Input name]

It's great to meet you {name}!
        """)
