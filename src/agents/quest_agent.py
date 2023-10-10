import logging

from steamship.agents.logging import AgentLogging
from steamship.agents.schema import Action, AgentContext
from steamship.agents.schema.action import FinishAction

from tools.end_quest_tool import EndQuestTool
from utils.context_utils import (
    await_ask,
    get_current_quest,
    get_game_state,
    save_game_state,
)
from utils.generation_utils import send_story_generation
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
        quest = get_current_quest(context)

        logging.info(
            "[DEBUG] Running Quest Agent",
            extra={
                AgentLogging.IS_MESSAGE: True,
                AgentLogging.MESSAGE_TYPE: AgentLogging.AGENT,
                AgentLogging.MESSAGE_AUTHOR: AgentLogging.TOOL,
                AgentLogging.AGENT_NAME: self.__class__.__name__,
            },
        )

        if not quest.sent_intro:
            logging.info(
                "[DEBUG] Sending Intro Part 1",
                extra={
                    AgentLogging.IS_MESSAGE: True,
                    AgentLogging.MESSAGE_TYPE: AgentLogging.AGENT,
                    AgentLogging.MESSAGE_AUTHOR: AgentLogging.TOOL,
                    AgentLogging.AGENT_NAME: self.__class__.__name__,
                },
            )

            send_story_generation(
                f"Like the narrator of a movie, explain that {player.name} is embarking on a quest. Speak briefly. Use only a few sentences.",
                context=context,
            )

            logging.info(
                "[DEBUG] Sending Intro Part 2",
                extra={
                    AgentLogging.IS_MESSAGE: True,
                    AgentLogging.MESSAGE_TYPE: AgentLogging.AGENT,
                    AgentLogging.MESSAGE_AUTHOR: AgentLogging.TOOL,
                    AgentLogging.AGENT_NAME: self.__class__.__name__,
                },
            )

            # send_background_music(prompt="Guitar music", context=context)
            # send_background_image(prompt="In a deep, dark forest", context=context)

            send_story_generation(
                f"{game_state.player.name} it about to go on a mission. Describe the first few things they do in a few sentences",
                context=context,
            )

            send_story_generation(
                f"How does this mission end? {player.name} should not yet achieve their overall goal of {game_state.player.motivation}",
                context=context,
            )
            quest.sent_intro = True
            save_game_state(game_state, context)
        else:
            logging.info(
                "[DEBUG] First Quest Story Block Skipped",
                extra={
                    AgentLogging.IS_MESSAGE: True,
                    AgentLogging.MESSAGE_TYPE: AgentLogging.AGENT,
                    AgentLogging.MESSAGE_AUTHOR: AgentLogging.TOOL,
                    AgentLogging.AGENT_NAME: self.__class__.__name__,
                },
            )

        if not quest.user_problem_solution:
            quest.user_problem_solution = await_ask(
                f"What does {player.name} do next?",
                context,
            )
            save_game_state(game_state, context)

        if not quest.sent_outro:
            send_story_generation(
                f"Explain how {player.name} solves things.",
                context=context,
            )
            quest.sent_outro = True
            save_game_state(game_state, context)

        blocks = EndQuestTool().run([], context)
        return FinishAction(output=blocks)
