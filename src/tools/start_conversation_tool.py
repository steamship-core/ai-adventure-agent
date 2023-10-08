import logging
from typing import Any, List, Optional, Union

from steamship import Block, Task
from steamship.agents.logging import AgentLogging
from steamship.agents.schema import AgentContext, Tool

from schema.characters import NpcCharacter
from schema.game_state import GameState
from utils.context_utils import get_game_state, save_game_state


class StartConversationTool(Tool):
    """Talks to an NPC.

    This Tool is meant to TRANSITION the user state to "in_dialogue" by modifying game_state and returning.

    It can either be called by:
     - The CAMP AGENT (when in full-chat mode) -- see camp_agent.py
     - The WEB APP (when in web-mode, via api) -- see camp_mixin.py
    """

    def __init__(self, **kwargs):
        kwargs["name"] = "TalkToSomeoneTool"
        kwargs[
            "agent_description"
        ] = "Use when the user wants to talk to someone. The input is the name of the person to talk to. Only use the tool if that person is present in the scene."
        kwargs[
            "human_description"
        ] = "Tool to initiate a conversation. Modifies the global state such that the in_conversation_with bit is set to a NPC name."
        # It always returns.. OK! Let's go!
        kwargs["is_final"] = True
        super().__init__(**kwargs)

    def log_error(self, msg: str):
        logging.error(
            msg,
            extra={
                AgentLogging.IS_MESSAGE: True,
                AgentLogging.MESSAGE_TYPE: AgentLogging.THOUGHT,
                AgentLogging.MESSAGE_AUTHOR: AgentLogging.TOOL,
                AgentLogging.TOOL_NAME: self.name,
            },
        )
        return msg

    def start_conversation(
        self,
        character_name: str,
        game_state: GameState,
        context: AgentContext,
    ) -> Union[str, NpcCharacter]:
        if not character_name:
            return self.log_error(
                "I couldn't figure out who you were trying to start a conversation with.",
            )

        if game_state.current_quest:
            return self.log_error(
                "You are currently on a quest. You can only start a chat back at camp.",
            )

        if game_state.in_conversation_with:
            return self.log_error(
                f"You are currently in a conversation with {game_state.in_conversation_with}. You can't start one with {character_name} until you leave that one.",
            )

        if not game_state.camp:
            return self.log_error(
                f"No camp object has been created. Unable to start a chat with {character_name}",
            )

        if not game_state.camp.npcs:
            return self.log_error(
                f"Nobody is at camp! Unable to start a chat with {character_name}",
            )

        npc: Optional[NpcCharacter] = None
        for char in game_state.camp.npcs:
            if character_name == char.name:
                npc = char
                break

        if not npc:
            all_names = ", ".join([npc.name for npc in game_state.camp.npcs])
            return self.log_error(
                f"Unable to start a chat with {character_name}. The only people in camp are {all_names}.",
            )

        # Finally.. we have our NPC.
        game_state.in_conversation_with = npc.name
        save_game_state(game_state, context)
        return npc

    def run(
        self, tool_input: List[Block], context: AgentContext
    ) -> Union[List[Block], Task[Any]]:
        character_name = None
        game_state = get_game_state(context)

        if tool_input:
            character_name = tool_input[0].text

        npc_or_error = self.start_conversation(character_name, game_state, context)

        if isinstance(npc_or_error, str):
            return [Block(text=npc_or_error)]
        else:
            player = game_state.player
            return [
                Block(
                    text=f"{player.name} walks up to {npc_or_error.name}. They look up, waiting for {player.name} to speak first."
                )
            ]
