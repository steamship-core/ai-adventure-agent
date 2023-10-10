import uuid
from typing import Any, List, Optional, Union

from steamship import Block, MimeTypes, Task
from steamship.agents.schema import AgentContext, ChatHistory, FinishAction, Tool

from schema.game_state import GameState
from schema.quest import Quest
from utils.context_utils import RunNextAgentException, get_game_state, save_game_state


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

        # quest = Quest(chat_file_id=f"quest-{uuid.uuid4()}")
        quest = Quest(
            chat_file_id=context.chat_history.file.id
        )  # TODO: This may need to change.

        player = game_state.player

        chat_history = ChatHistory.get_or_create(
            context.client, {"id": quest.chat_file_id}
        )

        quest_kickoff_messages = []

        quest_kickoff_messages.append(
            f"We are writing a story about the adventure of a character named {player.name}."
        )

        if player.background:
            quest_kickoff_messages.append(
                f"{player.name} has the following background: {player.background}"
            )

        # Add in information about pinventory
        if player.inventory:
            items = []
            for item in player.inventory or []:
                items.append(item.name)
            if len(items) > 0:
                item_list = ",".join(items)
                quest_kickoff_messages.append(
                    f"{player.name} has the following things in their inventory: {item_list}"
                )

        if player.motivation:
            quest_kickoff_messages.append(
                f"{player.name}'s motivation is to {player.motivation}"
            )

        if game_state.tone:
            quest_kickoff_messages.append(
                f"The tone of this story is {game_state.tone}"
            )

        # Add in information about prior quests
        prepared_mission_summaries = []
        if game_state.quests:
            for prior_quest in game_state.quests or []:
                if prior_quest.text_summary is not None:
                    prepared_mission_summaries.append(prior_quest.text_summary)

            if len(prepared_mission_summaries) > 0:
                quest_kickoff_messages.append(
                    f"{player.name} has already been on previous missions: \n {prepared_mission_summaries}"
                )

        chat_history.append_system_message("\n".join(quest_kickoff_messages))

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
                        text=f"{player.name} gathers his items and prepares to embark on a quest..",
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
