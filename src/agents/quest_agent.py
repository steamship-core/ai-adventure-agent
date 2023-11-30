import json
import logging
from datetime import datetime, timezone
from enum import Enum
from random import randint, random
from typing import Dict, List

from steamship import Tag
from steamship.agents.logging import AgentLogging
from steamship.agents.schema import Action, AgentContext
from steamship.agents.schema.action import FinishAction

from generators.generator_context_utils import (
    get_camp_image_generator,
    get_music_generator,
)
from schema.game_state import GameState
from schema.quest import Quest, QuestDescription
from schema.server_settings import Difficulty
from tools.end_quest_tool import EndQuestTool
from utils.context_utils import (
    FinishActionException,
    await_ask,
    get_current_quest,
    get_game_state,
    get_server_settings,
    save_game_state,
)
from utils.generation_utils import (
    await_streamed_block,
    generate_likelihood_estimation,
    generate_quest_arc,
    send_story_generation,
)
from utils.interruptible_python_agent import InterruptiblePythonAgent
from utils.moderation_utils import mark_block_as_excluded
from utils.tags import InstructionsTag, QuestIdTag, QuestTag, TagKindExtensions


class Likelihood(str, Enum):
    VERY_LIKELY = "VERY_LIKELY"
    LIKELY = "LIKELY"
    UNKNOWN = "UNKNOWN"
    UNLIKELY = "UNLIKELY"
    VERY_UNLIKELY = "VERY_UNLIKELY"


LIKELIHOOD_MAP: Dict[Difficulty, Dict[Likelihood, float]] = {
    Difficulty.EASY: {
        Likelihood.VERY_LIKELY: 0.05,
        Likelihood.LIKELY: 0.2,
        Likelihood.UNKNOWN: 0.35,
        Likelihood.UNLIKELY: 0.55,
        Likelihood.VERY_UNLIKELY: 0.7,
    },
    Difficulty.NORMAL: {
        Likelihood.VERY_LIKELY: 0.1,
        Likelihood.LIKELY: 0.3,
        Likelihood.UNKNOWN: 0.5,
        Likelihood.UNLIKELY: 0.7,
        Likelihood.VERY_UNLIKELY: 0.9,
    },
    Difficulty.HARD: {
        Likelihood.VERY_LIKELY: 0.2,
        Likelihood.LIKELY: 0.35,
        Likelihood.UNKNOWN: 0.6,
        Likelihood.UNLIKELY: 0.8,
        Likelihood.VERY_UNLIKELY: 0.95,
    },
}


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
        server_settings = get_server_settings(context)

        if not game_state.quest_arc:
            game_state.quest_arc = generate_quest_arc(game_state.player, context)

        if len(game_state.quest_arc) >= len(game_state.quests):
            quest_description = game_state.quest_arc[len(game_state.quests) - 1]
        else:
            logging.warning("QUEST DESCRIPTION IS NONE.")
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
                optional_desc = ""
                if (
                    quest_description.description
                    and quest_description.description.strip()
                ):
                    optional_desc = f"\n\nAuthor's notes for this quest are: {quest_description.description}"

                context.chat_history.append_system_message(
                    text=f"{game_state.player.name} is embarking on a quest to {quest_description.goal} "
                    f"at {quest_description.location}.{optional_desc}",
                    tags=[
                        Tag(
                            kind=TagKindExtensions.INSTRUCTIONS,
                            name=InstructionsTag.QUEST,
                        ),
                        QuestIdTag(quest_id=quest.name),
                    ],
                )
                num_paragraphs = randint(1, 1)  # noqa: S311
                prompt = (
                    f"Generate the introduction to the quest in {num_paragraphs} short paragraph(s). "
                    f"DO NOT present {game_state.player.name} with a challenge or obstacle in this description. "
                    f"Just set the scene. "
                    f"{game_state.player.name} MUST NOT achieve their goal in the generated paragraphs. "
                    f"Tell the story using a tone of '{server_settings.narrative_tone}' and with a narrative voice of "
                    f"'{server_settings.narrative_voice}'."
                )
            else:
                # here as a fallback
                num_paragraphs = randint(1, 1)  # noqa: S311
                prompt = (
                    f"{game_state.player.name} is embarking on a quest. Describe the first few things they do "
                    f"in {num_paragraphs} short paragraph(s)."
                )
            block = send_story_generation(
                prompt=prompt,
                quest_name=quest.name,
                context=context,
            )
            await_streamed_block(block, context)

            self.create_problem(
                game_state, context, quest, quest_description=quest_description
            )

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
                    self.generate_solution(
                        game_state, context, quest, quest_description.goal
                    )
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
                    logging.exception(e)

                    prologue_msg = (
                        "Our Apologies: Something went wrong with writing the next part of the story. "
                        "Let's try again."
                    )

                    if "flagged" in str(e):
                        prologue_msg = "That response triggered the game’s content moderation filter. Please try again."
                        # flag original message as excluded (this will prevent "getting stuck")
                        if message := context.chat_history.last_user_message:
                            mark_block_as_excluded(message)

                        # clear last sys message added by generate_solution (that copies the user submitted solution)
                        if sys_message := context.chat_history.last_system_message:
                            mark_block_as_excluded(sys_message)

                    logging.error(f"Sent to user: {prologue_msg}")

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
                self.create_problem(
                    game_state, context, quest, quest_description=quest_description
                )
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
                prompt = (
                    f"Complete the story of the {player.name}'s current quest in 3 or fewer paragraphs. {player.name} should achieve "
                    f"the goal of '{quest_description.goal}', but NOT their overall goal of {server_settings.adventure_goal}. "
                    f"Tell the story using a tone of '{server_settings.narrative_tone}' and with a narrative voice of "
                    f"'{server_settings.narrative_voice}'."
                )
            else:
                prompt = (
                    f"Complete the story of the {player.name}'s current quest in 3 or fewer paragraphs. {player.name} should not yet "
                    f"achieve their overall goal of '{server_settings.adventure_goal}'. "
                    f"Tell the story using a tone of '{server_settings.narrative_tone}' and with a narrative voice of "
                    f"'{server_settings.narrative_voice}'."
                )
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
        self,
        game_state: GameState,
        context: AgentContext,
        quest: Quest,
        quest_description: QuestDescription,
    ):
        if len(quest.user_problem_solutions) == quest.num_problems_to_encounter - 1:
            # if last problem, try to make it make sense for wrapping things up
            num_paragraphs = randint(1, 2)  # noqa: S311
            server_settings = get_server_settings(context=context)
            prompt = (
                f"Continue telling the story, in a tone of '{server_settings.narrative_tone}' with a narrative voice of "
                f"{server_settings.narrative_voice}, of {game_state.player.name}'s quest. Write about them encountering a "
                f"challenge that prevents them from completing their current quest.\n"
                f"DO NOT use the word 'challenge' directly.\n"
                f"DO NOT mention any sort of ordering of challenges (examples: 'first' or 'next').\n"
                f"DO NOT solve the challenge for {game_state.player.name}.\n"
                f"The story should allow {game_state.player.name} to decide how to attempt to complete their "
                f"quest. The story MUST continue the current story arc of the quest.\n"
                f"Write exactly {num_paragraphs} short paragraph(s) in the tone of {server_settings.narrative_tone} "
                f"with {server_settings.narrative_voice}."
            )
        else:
            num_paragraphs = randint(1, 2)  # noqa: S311
            server_settings = get_server_settings(context=context)
            prompt = (
                f"Tell the story using a tone of '{server_settings.narrative_tone}' with a narrative voice of "
                f"{server_settings.narrative_voice} of {game_state.player.name} encountering a challenge on their "
                f"current quest ({quest_description.location}, {quest_description.goal}).\n"
                f"The challenge MUST NOT repeat (or be equivalent to) a prior challenge faced by "
                f"{game_state.player.name}.\n"
                f"DO NOT introduce more than one problem.\n"
                f"DO NOT use the words 'challenge' or 'problem' directly.\n"
                f"DO NOT mention any sort of ordering of challenges (examples: 'first' or 'next').\n"
                f"DO NOT solve the challenge for {game_state.player.name}.\n"
                f"The story MUST continue the current story arc of the quest. The story SHOULD allow "
                f"{game_state.player.name} to decide how to attempt to solve the challenge.\n"
                f"Write exactly {num_paragraphs} short paragraph(s) in the tone of {server_settings.narrative_tone} "
                f"with {server_settings.narrative_voice}."
            )
        problem_block = send_story_generation(
            prompt=prompt,
            quest_name=quest.name,
            context=context,
        )
        updated_problem_block = await_streamed_block(problem_block, context)

        if image_gen := get_camp_image_generator(context):
            image_gen.request_scene_image_generation(
                description=updated_problem_block.text, context=context
            )
        if music_gen := get_music_generator(context):
            music_gen.request_scene_music_generation(
                description=updated_problem_block.text, context=context
            )

    def evaluate_solution(
        self, game_state: GameState, context: AgentContext, quest: Quest
    ):
        server_settings = get_server_settings(context)
        prompt = (
            f"{game_state.player.name} tries to solve the problem by: {quest.user_problem_solutions[-1]}. "
            f"How likely is this to succeed? "
            f"Please consider their abilities and whether any referenced objects are nearby or in their inventory. "
            f"ONLY RESPOND WITH ONE OF [VERY UNLIKELY, UNLIKELY, LIKELY, VERY LIKELY]"
        )
        likelihood_block = generate_likelihood_estimation(
            prompt=prompt,
            quest_name=quest.name,
            context=context,
        )
        likelihood_text = likelihood_block.text.upper()
        likelihood_map = LIKELIHOOD_MAP.get(server_settings.difficulty)
        if "VERY UNLIKELY" in likelihood_text:
            required_roll = likelihood_map[Likelihood.VERY_UNLIKELY]
        elif "VERY LIKELY" in likelihood_text:
            required_roll = likelihood_map[Likelihood.VERY_LIKELY]
        elif "UNLIKELY" in likelihood_text:
            required_roll = likelihood_map[Likelihood.UNLIKELY]
        elif "LIKELY" in likelihood_text:
            required_roll = likelihood_map[Likelihood.LIKELY]
        else:
            required_roll = likelihood_map[Likelihood.UNKNOWN]

        # Add minor randomness, but don't drop below 0.05 (2 on d20) or go above 0.95 (20 on d20)
        required_roll_mod = 0.05 * (randint(-2, 2))
        required_roll = min(0.95, max(0.05, required_roll + required_roll_mod))
        # make sure we don't get weird floating point near values
        required_roll = round(required_roll, 2)

        roll = random()  # noqa: S311
        succeeded = roll > required_roll
        dice_roll_message = json.dumps(
            {
                "required": required_roll,
                "rolled": roll,
                "success": succeeded,
                "mod": required_roll_mod,
            }
        )
        context.chat_history.append_system_message(
            dice_roll_message, tags=self.tags(QuestTag.DICE_ROLL, quest)
        )
        return succeeded

    def generate_solution(
        self,
        game_state: GameState,
        context: AgentContext,
        quest: Quest,
        quest_goal: str,
    ):
        num_paragraphs = randint(1, 2)  # noqa: S311
        server_settings = get_server_settings(context=context)
        prompt = (
            f"{game_state.player.name} tries to solve the problem by: {quest.user_problem_solutions[-1]}, and it totally works.\n"
            f"Describe what happens in {num_paragraphs} short paragraphs. As part of the description, DO NOT have "
            f"{game_state.player.name} completing the quest goal of {quest_goal}. "
            f"Tell the story using a tone of {server_settings.narrative_tone} and with a narrative voice of "
            f"{server_settings.narrative_voice}."
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
        num_paragraphs = randint(1, 2)  # noqa: S311
        server_settings = get_server_settings(context=context)
        prompt = (
            f"{game_state.player.name} tries to solve the problem by: {quest.user_problem_solutions[-1]}, and it fails.\n"
            f"Describe what happens in {num_paragraphs} short paragraphs. "
            f"Tell the story using a tone of {server_settings.narrative_tone} and with a narrative voice of "
            f"{server_settings.narrative_voice}."
        )
        solution_block = send_story_generation(
            prompt=prompt,
            quest_name=quest.name,
            context=context,
        )
        await_streamed_block(solution_block, context)
