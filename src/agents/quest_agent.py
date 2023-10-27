import logging
from datetime import datetime, timezone
from random import random
from typing import List

from steamship import Tag
from steamship.agents.logging import AgentLogging
from steamship.agents.schema import Action, AgentContext
from steamship.agents.schema.action import FinishAction

from generators.generator_context_utils import get_image_generator, get_music_generator
from schema.game_state import GameState
from schema.quest import Quest, QuestDescription
from tools.end_quest_tool import EndQuestTool
from utils.context_utils import (
    await_ask,
    get_current_quest,
    get_game_state,
    save_game_state, FinishActionException,
)
from utils.generation_utils import (
    await_streamed_block,
    generate_quest_arc,
    send_story_generation,
)
from utils.interruptible_python_agent import InterruptiblePythonAgent
from utils.moderation_utils import mark_block_as_excluded
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

    def run(self, context: AgentContext) -> Action:  # noqa: C901
        """
        It could go in a tool, but that doesn't feel necessary... there are some other spots where tools feel very
        well fit, but this might be better left open-ended, so we can stop/start things as we like.
        """

        # Load the main things we're working with. These can modified and the save_game_state called at any time
        game_state = get_game_state(context)
        player = game_state.player
        quest = get_current_quest(context)

        if not game_state.quest_arc:
            game_state.quest_arc = generate_quest_arc(game_state.player, context)

        if len(game_state.quest_arc) >= len(game_state.quests):
            quest_description = game_state.quest_arc[len(game_state.quests) - 1]
        else:
            quest_description = None

        logging.debug(
            "Running Quest Agent",
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

            logging.debug(
                "Sending Intro Part 2",
                extra={
                    AgentLogging.IS_MESSAGE: True,
                    AgentLogging.MESSAGE_TYPE: AgentLogging.AGENT,
                    AgentLogging.MESSAGE_AUTHOR: AgentLogging.TOOL,
                    AgentLogging.AGENT_NAME: self.__class__.__name__,
                },
            )

            if quest_description is not None:
                prompt = f"{game_state.player.name} is about to go on a mission to {quest_description.goal} at {quest_description.location}. Describe the first few things they do in a few sentences"
            else:
                # here as a fallback
                prompt = f"{game_state.player.name} is about to go on a mission. Describe the first few things they do in a few sentences"
            block = send_story_generation(
                prompt=prompt,
                quest_name=quest.name,
                context=context,
            )
            await_streamed_block(block, context)

            self.create_problem(game_state, context, quest, quest_description=quest_description)

            save_game_state(game_state, context)
        else:
            logging.debug(
                "First Quest Story Block Skipped",
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
            try:
                if self.evaluate_solution(game_state, context, quest):
                    # TODO: tag last user message as solution
                    self.generate_solution(game_state, context, quest)
                else:
                    self.describe_failure(game_state, context, quest)
                    quest.user_problem_solutions.pop()
                    quest.user_problem_solutions.append(
                        await_ask(
                            f"What does {player.name} do next?",
                            context=context,
                            key_suffix=f"{quest.name} solution {len(quest.user_problem_solutions)}",
                        )
                    )
            except Exception as e:
                if isinstance(e, FinishActionException):
                    raise e
                else:
                    prologue_msg = (
                        "Our Apologies: Something went wrong with writing the next part of the story. "
                        "Let's try again."
                    )
                    # TODO(doug): do we want to indicate the input was flagged if that is the issue?
                    if "flagged" in str(e):
                        prologue_msg = "That response triggered the game’s content moderation filter. Please try again."
                        # flag original message as excluded (this will prevent "getting stuck")
                        if message := context.chat_history.last_user_message:
                            mark_block_as_excluded(message)

                        # clear last sys message added by generate_solution (that copies the user submitted solution)
                        if sys_message := context.chat_history.last_system_message:
                            mark_block_as_excluded(sys_message)

                    # undo the game solution state, and start over
                    # todo: should we consider using a Command design pattern-like approach here for undo?
                    quest.user_problem_solutions.pop()
                    quest.user_problem_solutions.append(
                        await_ask(
                            f"What does {player.name} do next?",
                            context=context,
                            key_suffix=f"{quest.name} solution {len(quest.user_problem_solutions)}",
                            prompt_prologue=prologue_msg,
                        )
                    )

            if len(quest.user_problem_solutions) != quest.num_problems_to_encounter:
                self.create_problem(game_state, context, quest, quest_description=quest_description)
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

            if quest_description is not None:
                prompt = f"How does this mission end? {player.name} should achieve their goal of {quest_description.goal}"
            else:
                prompt = f"How does this mission end? {player.name} should not yet achieve their overall goal of {game_state.player.motivation}"
            story_end_block = send_story_generation(
                prompt,
                quest_name=quest.name,
                context=context,
            )
            await_streamed_block(story_end_block, context)

        quest.completed_timestamp = datetime.now(timezone.utc).isoformat()

        blocks = EndQuestTool().run([], context)
        return FinishAction(output=blocks)

    def tags(self, part: QuestTag, quest: "Quest") -> List[Tag]:  # noqa: F821
        return [Tag(kind=TagKindExtensions.QUEST, name=part), QuestIdTag(quest.name)]

    def create_problem(
        self, game_state: GameState, context: AgentContext, quest: Quest, quest_description: QuestDescription
    ):
        if len(quest.user_problem_solutions) == quest.num_problems_to_encounter -1:
            # if last problem, try to make it make sense for wrapping things up
            prompt = f"Describe the last problem {game_state.player.name} needs to overcome in order to finish the quest: {quest_description.goal}."
        else:
            prompt = f"Oh no! {game_state.player.name} encounters a new problem. Describe the problem."
        problem_block = send_story_generation(
            prompt=prompt,
            quest_name=quest.name,
            context=context,
        )
        updated_problem_block = await_streamed_block(problem_block, context)

        if image_gen := get_image_generator(context):
            image_gen.request_scene_image_generation(
                description=updated_problem_block.text, context=context
            )
        if music_gen := get_music_generator(context):
            music_gen.request_scene_music_generation(
                description=updated_problem_block.text, context=context
            )

    def evaluate_solution(self, game_state: GameState, context: AgentContext, quest: Quest):
        prompt = (
            f"{game_state.player.name} tries to solve the problem by: {quest.user_problem_solutions[-1]}. How likely is this to succeed? "
            f"Please consider their abilities and whether any referenced objects are nearby or in their inventory."
            f"Respond with VERY UNLIKELY, UNLIKELY, LIKELY, OR VERY LIKELY."
        )
        likelihood_block = send_story_generation(
            prompt=prompt,
            quest_name=quest.name,
            context=context,
        )
        await_streamed_block(likelihood_block, context)
        likelihood_text = likelihood_block.text.upper()
        if likelihood_text.startswith("VERY UNLIKELY"):
            required_roll = 0.9
        elif likelihood_text.startswith("UNLIKELY"):
            required_roll = 0.7
        elif likelihood_text.startswith("LIKELY"):
            required_roll = 0.3
        elif likelihood_text.startswith("VERY LIKELY"):
            required_roll = 0.1
        else:
            required_roll = 0.5
        roll = random()
        succeeded = roll > required_roll
        context.chat_history.append_system_message(f"{game_state.player.name} needed to roll a {required_roll}, and rolled {roll}. Success: {succeeded}")
        return succeeded



    def generate_solution(
        self, game_state: GameState, context: AgentContext, quest: Quest
    ):
        prompt = (
            f"{game_state.player.name} tries to solve the problem by: {quest.user_problem_solutions[-1]}, and it totally works.\n"
            f"Describe what happens."
        )
        solution_block = send_story_generation(
            prompt=prompt,
            quest_name=quest.name,
            context=context,
        )
        await_streamed_block(solution_block, context)

    def describe_failure(
        self, game_state: GameState, context: AgentContext, quest: Quest
    ):
        prompt = (
            f"{game_state.player.name} tries to solve the problem by: {quest.user_problem_solutions[-1]}, and it fails.\n"
            f"Describe what happens."
        )
        solution_block = send_story_generation(
            prompt=prompt,
            quest_name=quest.name,
            context=context,
        )
        await_streamed_block(solution_block, context)
