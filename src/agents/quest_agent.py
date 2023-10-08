from steamship.agents.schema import Action, AgentContext
from steamship.agents.schema.action import FinishAction

from tools.end_quest_tool import EndQuestTool
from utils.context_utils import get_game_state
from utils.generation_utils import (
    send_background_image,
    send_background_music,
    send_story_generation,
)
from utils.interruptible_python_agent import InterruptiblePythonAgent


class QuestAgent(InterruptiblePythonAgent):
    """
    The quest agent goes on a quest!

    HOW THIS AGENT IS ACTIVATED
    ===========================

    The game log defers to this agent when `game_state.current_quest` is not None.

    The `game_state.current_quest` argument matches `game_state.quests[].name` and is used to provide the
    Quest object to this agent at construction time so that it has a handle on where to load/store state.

    WHAT CAUSES THAT ACTIVATION TO HAPPEN
    =====================================

    The `use_settings.current_quest` string is set to not-None when the following things happen:

    - POST /start_quest (See the quest_mixin)
    - maybe later: The Camp Agent runs the Start Quest Tool

    It can be slotted into as a state machine sub-agent by the overall agent.
    """

    def run(self, context: AgentContext) -> Action:
        """
        It could go in a tool, but that doesn't feel necessary.. there are some other spots where tools feel very
        well fit, but this might be better left open-ended so we can stop/start things as we like.
        """

        # Load the main things we're working with. These can modified and the save_game_state called at any time
        game_state = get_game_state(context)
        player = game_state.player
        # quest = get_current_quest(context)

        # Note:
        #    We don't generate directly into the ChatHistory file because we can't yet add the right tags along
        send_story_generation(
            f"Like the narrator of a movie, explain that {player.name} is embarking on a quest. Speak briefly. Use only a few sentences.",
            context=context,
        )

        send_background_music(prompt="Guitar music", context=context)
        send_background_image(prompt="In a deep, dark forest", context=context)

        send_story_generation(
            f"{game_state.player.name} it about to go on a mission. Describe the first few things they do in a few sentences",
            context=context,
        )

        send_story_generation(
            f"How does this mission end? {player.name} should not yet achieve their overall goal of {game_state.player.motivation}",
            context=context,
        )

        blocks = EndQuestTool().run([], context)
        return FinishAction(output=blocks)
