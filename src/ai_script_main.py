from typing import List, Optional, Type, cast
from steamship import Steamship, SteamshipError
from steamship.utils.repl import AgentREPL

from gendown.ai_script_agent import AiScriptAgent
from gendown.gendown_parser import parse_gendown
from utils.agent_service import AgentService

class AiScriptMain(AgentService):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Paste markdown from the /ai_scripts directory!
        self.set_default_agent(AiScriptAgent("""
# Welcome

Welcome!

Gendown is a Markdown-based format for creating AI Storytelling adventures.

Write in a text editor, on you phone, in Notion... and then use it in any game or storybook that supports it.

You're reading GenDown right now!
        """))

if __name__ == "__main__":
    # client = Steamship(workspace="thing-crater-i8mli")
    # repl = AgentREPL(
    #     cast(AgentService, AiScriptMain), agent_package_config={}, client=client
    # )
    # repl.run(dump_history_on_exit=True)

    parse_gendown("""
# Welcome

[Generate] Welcome!

Gendown is a Markdown-based format for creating AI Storytelling adventures.

Write in a text editor, on you phone, in Notion... and then use it in any game or storybook that supports it.

You're reading GenDown right now!
        """)
