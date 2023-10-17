import uuid
from typing import Any, List, Optional, Union

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
        ] = "Tool to initiate a quest. Modifies the global state such that the next time the agent is contacted, it will be on a quets."
        # It always returns.. OK! Let's go!
        kwargs["is_final"] = True
        super().__init__(**kwargs)

    def start_quest(  # noqa: C901
        self,
        game_state: GameState,
        context: AgentContext,
        purpose: Optional[str] = None,
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
        game_state.quests.append(quest)

        quest.name = f"{uuid.uuid4()}"

        print(f"Current quest name is: {quest.name}")
        game_state.current_quest = quest.name

        # This saves it in a way that is both persistent (KV Store) and updates the context
        save_game_state(game_state, context)

        return quest

    def run(
        self, tool_input: List[Block], context: AgentContext
    ) -> Union[List[Block], Task[Any]]:
        purpose = None
        game_state = get_game_state(context)

        if tool_input:
            purpose = tool_input[0].text

        self.start_quest(game_state, context, purpose)

        player = game_state.player

        raise RunNextAgentException(
            action=FinishAction(
                input=[
                    Block(
                        text=f"", # Empty string here to not interfere with prompts in quest_agent
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
