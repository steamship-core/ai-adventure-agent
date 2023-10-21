from typing import List

from steamship import Block, MimeTypes, Tag
from steamship.agents.schema import Action, AgentContext, Tool
from steamship.agents.schema.action import FinishAction

from gendown.utils import get_markdown, set_markdown
from generators.generator_context_utils import get_image_generator, get_music_generator
from generators.utils import find_new_block
from schema.characters import HumanCharacter
from schema.game_state import GameState
from utils.context_utils import (
    RunNextAgentException,
    await_ask,
    get_game_state,
    save_game_state,
)
from utils.interruptible_python_agent import InterruptiblePythonAgent
from utils.tags import CampTag, CharacterTag, StoryContextTag, TagKindExtensions


class AiScriptAgent(InterruptiblePythonAgent):
    """Implements the flow to onboared a new player.

    - For pure chat users, this is essential.
    - For web users, this is not necessary, as the website will provide this information via API.

    This flow uses checks against the game_state object to fast-forward through this logic in such that only
    the missing pieces of information are asked of the user in either chat or web mode.
    """
    tools: List[Tool] = []
    md: str

    def __init__(self, *args, md: str = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.md = md

    def run(self, context: AgentContext) -> Action:  # noqa: C901

        return FinishAction(output=[Block(text="")])
