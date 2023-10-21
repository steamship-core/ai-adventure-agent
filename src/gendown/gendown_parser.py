from enum import Enum
from typing import List, Optional
from marko import Markdown
from marko.block import BlankLine, Heading, Paragraph, CodeBlock
from marko.element import Element
from marko.md_renderer import MarkdownRenderer
import re
from pydantic import BaseModel, Field
from steamship.agents.schema import AgentContext


class NodeKind(str, Enum):
    scope = "scope"
    output = "output"
    command = "command"

class AstNode(BaseModel):
    id: Optional[str] = Field("", description="Id. Used for resume!")
    text: Optional[str] = Field("", description="The content")
    kind: Optional[str] = Field("", description="")
    command: Optional[str] = Field("", description="The comamnd, if kind is command")
    inline_command_arg: Optional[str] = Field("")
    children: Optional[List["AstNode"]]

    def visit(self, context: AgentContext):
        if self.kind == NodeKind.output:
            asdf

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

                return AstNode(
                    kind=NodeKind.command,
                    command=command_parts[0].strip(),
                    inline_command_arg=" ".join(command_parts[1:]).strip(),
                    text=default_argument.strip()
                )
    return None


def parse_gendown(text: str) -> List[AstNode]:
    markdown = Markdown(extensions=[])

    md = markdown.parse(text)
    ret = []

    cursor = AstNode(kind=NodeKind.output)

    def reduce():
        nonlocal ret
        nonlocal cursor
        if cursor.text:
            cursor.text = cursor.text.strip()
            ret.append(cursor)
        cursor = AstNode(kind=NodeKind.output)

    renderer = MarkdownRenderer()
    renderer.__enter__()

    for child in md.children:
        if cmd := is_command(child):
            reduce()
            ret.append(cmd)
        elif is_output(child):
            cursor.text += renderer.render(child)
    reduce()


    return ret



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
