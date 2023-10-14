import logging
from typing import List

from steamship import Tag
from steamship.agents.logging import AgentLogging
from steamship.agents.schema import Action, AgentContext
from steamship.agents.schema.action import FinishAction

from generators.generator_context_utils import get_image_generator
from tools.end_quest_tool import EndQuestTool
from utils.context_utils import (
    await_ask,
    get_current_quest,
    get_game_state,
    save_game_state,
)
from utils.generation_utils import await_streamed_block, send_story_generation
from utils.interruptible_python_agent import InterruptiblePythonAgent
from utils.tags import QuestTag, TagKindExtensions


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
            quest.sent_intro = True
            save_game_state(game_state, context)

            logging.info(
                "[DEBUG] Sending Intro Part 2",
                extra={
                    AgentLogging.IS_MESSAGE: True,
                    AgentLogging.MESSAGE_TYPE: AgentLogging.AGENT,
                    AgentLogging.MESSAGE_AUTHOR: AgentLogging.TOOL,
                    AgentLogging.AGENT_NAME: self.__class__.__name__,
                },
            )

            block = send_story_generation(
                f"{game_state.player.name} is about to go on a mission. Describe the first few things they do in a few sentences",
                quest_name=quest.name,
                context=context,
            )
            await_streamed_block(block)
            problem_block = send_story_generation(
                f"Oh no! {game_state.player.name} encounters a problem. Describe the problem.",
                quest_name=quest.name,
                context=context,
            )
            updated_problem_block = await_streamed_block(problem_block)

            if image_gen := get_image_generator(context):
                image_gen.request_scene_image_generation(
                    description=updated_problem_block.text, context=context
                )
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
            quest.sent_outro = True
            save_game_state(game_state, context)

            # TODO: Dave I switched this to a system message so it wouldn't be played back to the user on top of the answer
            # they gave -- does that mess with anything from your perspective?
            context.chat_history.append_system_message(
                text=f"{player.name} solves the problem by: {quest.user_problem_solution}",
                tags=self.tags(QuestTag.USER_SOLUTION, quest),
            )
            story_end_block = send_story_generation(
                f"How does this mission end? {player.name} should not yet achieve their overall goal of {game_state.player.motivation}",
                quest_name=quest.name,
                context=context,
            )
            await_streamed_block(story_end_block)

        blocks = EndQuestTool().run([], context)
        return FinishAction(output=blocks)

    def tags(self, part: QuestTag, quest: "Quest") -> List[Tag]:  # noqa: F821
        return [
            Tag(kind=TagKindExtensions.QUEST, name=part),
            Tag(
                kind=TagKindExtensions.QUEST,
                name=QuestTag.QUEST_ID,
                value={"id": quest.name},
            ),
        ]
