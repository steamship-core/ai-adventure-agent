import logging
from datetime import datetime, timezone
from typing import List

from steamship import Tag
from steamship.agents.logging import AgentLogging
from steamship.agents.schema import Action, AgentContext
from steamship.agents.schema.action import FinishAction

from generators.generator_context_utils import get_image_generator, get_music_generator
from schema.game_state import GameState
from schema.quest import Quest
from tools.end_quest_tool import EndQuestTool
from utils.context_utils import (
    await_ask,
    get_current_quest,
    get_game_state,
    save_game_state,
)
from utils.generation_utils import await_streamed_block, send_story_generation
from utils.interruptible_python_agent import InterruptiblePythonAgent
from utils.tags import QuestIdTag, QuestTag, TagKindExtensions


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

            self.create_problem(game_state, context, quest)

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

        if len(quest.user_problem_solutions) != quest.num_problems_to_encounter:
            quest.user_problem_solutions.append(
                await_ask(
                    f"What does {player.name} do next?",
                    context,
                    key_suffix=f"{quest.name} solution {len(quest.user_problem_solutions)}",
                )
            )
            save_game_state(game_state, context)
            self.generate_solution(game_state, context, quest)
            if len(quest.user_problem_solutions) != quest.num_problems_to_encounter:
                self.create_problem(game_state, context, quest)
                quest.user_problem_solutions.append(
                    await_ask(
                        f"What does {player.name} do next?",
                        context,
                        key_suffix=f"{quest.name} solution {len(quest.user_problem_solutions)}",
                    )
                )

        if not quest.sent_outro:
            quest.sent_outro = True
            save_game_state(game_state, context)

            story_end_block = send_story_generation(
                f"How does this mission end? {player.name} should not yet achieve their overall goal of {game_state.player.motivation}",
                quest_name=quest.name,
                context=context,
            )
            await_streamed_block(story_end_block)

        quest.completed_timestamp = datetime.now(timezone.utc).isoformat()

        blocks = EndQuestTool().run([], context)
        return FinishAction(output=blocks)

    def tags(self, part: QuestTag, quest: "Quest") -> List[Tag]:  # noqa: F821
        return [Tag(kind=TagKindExtensions.QUEST, name=part), QuestIdTag(quest.name)]

    def create_problem(
        self, game_state: GameState, context: AgentContext, quest: Quest
    ):
        problem_block = send_story_generation(
            f"Oh no! {game_state.player.name} encounters a new problem. Describe the problem.",
            quest_name=quest.name,
            context=context,
        )
        updated_problem_block = await_streamed_block(problem_block)

        if image_gen := get_image_generator(context):
            image_gen.request_scene_image_generation(
                description=updated_problem_block.text, context=context
            )
        if music_gen := get_music_generator(context):
            music_gen.request_scene_music_generation(
                description=updated_problem_block.text, context=context
            )

    def generate_solution(
        self, game_state: GameState, context: AgentContext, quest: Quest
    ):
        context.chat_history.append_system_message(
            text=f"{game_state.player.name} tries to solve the problem by: {quest.user_problem_solutions[-1]}",
            tags=self.tags(QuestTag.USER_SOLUTION, quest),
        )
        send_story_generation(
            "What happens next? Does it work?",
            quest_name=quest.name,
            context=context,
        )
