import math
import uuid
from random import randint
from typing import Any, List, Union

from steamship import Block, MimeTypes, SteamshipError, Task
from steamship.agents.schema import AgentContext, FinishAction, Tool

from schema.game_state import GameState
from schema.quest import Quest
from schema.server_settings import ServerSettings
from utils.context_utils import (
    RunNextAgentException,
    get_game_state,
    get_server_settings,
    save_game_state,
)


class StartQuestTool(Tool):
    """Starts a quest.

    This Tool is meant to TRANSITION from the CAMP AGENT to the QUEST AGENT.

    It can either be called by:
     - The CAMP AGENT (when in full-chat mode) -- see camp_agent.py
     - The WEB APP (when in web-mode, via api) -- see quest_mixin.py

    This Tool does the following things:
    - Creates a new QUEST and CHAT HISTORY
    - Sets the GAME STATE to that QUEST
    - Seeds the CHAT HISTORY with system messages related to the overall game GAME STATE.

    That's it. All other interactions, which may involve asking the user questions or dynamically generating assets,
    are handled by the QUEST AGENT. This includes naming the quest, picking a location, etc etc.

    That keeps tools simple -- as objects whose purpose is to transition -- and leaves the Agents as objects that
    have more complex logic with conditionals / user-interrupt behavior / etc.
    """

    def __init__(self, **kwargs):
        kwargs["name"] = "StartQuestTool"
        kwargs[
            "agent_description"
        ] = "Use when the user wants to go on a quest. The input is the kind of quest, if provided. The output is the Quest Name"
        kwargs[
            "human_description"
        ] = "Tool to initiate a quest. Modifies the global state such that the next time the agent is contacted, it will be on a quest."
        # It always returns.. OK! Let's go!
        kwargs["is_final"] = True
        super().__init__(**kwargs)

    def start_quest(  # noqa: C901
        self,
        game_state: GameState,
        context: AgentContext,
    ) -> Quest:
        server_settings: ServerSettings = get_server_settings(context)
        player = game_state.player

        if player.energy < server_settings.quest_cost:
            raise SteamshipError(
                message=f"Going on a quest costs {server_settings.quest_cost} energy, but you only have {player.energy}."
            )

        # quest = Quest(chat_file_id=f"quest-{uuid.uuid4()}")
        chat_history = context.chat_history

        quest = Quest(
            chat_file_id=chat_history.file.id,
            # For now a quest is a fixed cost, controlled by the server settings.
            energy_delta=server_settings.quest_cost,
        )

        # Now save the chat history file
        quest.chat_file_id = chat_history.file.id

        if not game_state.quests:
            game_state.quests = []

        # If the last quest was a FAILURE then we will remove it from the list of quests. "Starting a Quest" in this case
        # means "Restarting that quest".
        # TODO(future): If we permit non-sequential playing of quests, we'll need to have an ID which means start
        # /which/ quest and possibly also an indicator of the user's intention to restart/retry a quest as opposed to
        # start from scratch.
        if game_state.quests and game_state.quests[-1].completed_success is False:
            # The last quest failed. Let's pop it from the list so that the quest we're starting will replace it.
            # At the moment, there's an implicit alignment between indices of `quests` and `quest_arcs` which is
            # why this action of popping this failed quest is identical to restarting the prior quest.
            game_state.quests.pop()

        game_state.quests.append(quest)

        quest_difficulty_base = 1
        if game_state.quest_arc is not None and len(game_state.quest_arc) >= len(
            game_state.quests
        ):
            quest_difficulty_base = len(game_state.quests)
        quest.num_problems_to_encounter = self.num_problems_to_encounter(
            quest_difficulty_base, server_settings
        )

        quest.name = f"{uuid.uuid4()}"

        print(f"Current quest name is: {quest.name}")
        game_state.current_quest = quest.name

        # This saves it in a way that is both persistent (KV Store) and updates the context
        save_game_state(game_state, context)

        return quest

    def num_problems_to_encounter(
        self, difficulty_base: int, server_settings: ServerSettings
    ) -> int:
        return (
            math.floor(difficulty_base * server_settings.problems_per_quest_scale)
            + server_settings.min_problems_per_quest
            + randint(0, server_settings.max_additional_problems_per_quest)
        )

    def run(
        self, tool_input: List[Block], context: AgentContext
    ) -> Union[List[Block], Task[Any]]:
        game_state = get_game_state(context)

        self.start_quest(game_state, context)

        player = game_state.player

        raise RunNextAgentException(
            action=FinishAction(
                input=[
                    Block(
                        text="",  # Empty string here to not interfere with prompts in quest_agent
                        mime_type=MimeTypes.MKD,
                    )
                ],
                output=[
                    Block(
                        text=f"{player.name} stands up.",
                        mime_type=MimeTypes.MKD,
                    )
                ],
            )
        )
