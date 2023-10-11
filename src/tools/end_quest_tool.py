import logging
from typing import Any, List, Union

from steamship import Block, Task
from steamship.agents.logging import AgentLogging
from steamship.agents.schema import AgentContext, Tool

from schema.game_state import GameState
from schema.objects import Item
from utils.context_utils import (
    get_current_quest,
    get_game_state,
    get_story_text_generator,
    save_game_state,
)
from utils.generation_utils import send_agent_status_message
from utils.tags import AgentStatusMessageTag


class EndQuestTool(Tool):
    """Ends the quest the player is on.

    This Tool is meant to TRANSITION the user state out of "questing" by modifying game_state and returning.

    It can either be called by:
     - The QUEST AGENT (when in full-chat mode) -- see quest_agent.py
       The QUEST AGENT is not a Function Calling agent, so it uses this tool manually!

     - The WEB APP (when in web-mode, via api) -- see quest_mixin.py
    """

    def __init__(self, **kwargs):
        kwargs["name"] = "EndQuestTool"
        kwargs[
            "agent_description"
        ] = "Use to exit a quest. Use this tool if someone says they want to end the quest or return to camp."
        kwargs[
            "human_description"
        ] = "Tool to leave a quest. Modifies the global state such that the current_quest bit is set to None."
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

    def end_quest(
        self,
        game_state: GameState,
        context: AgentContext,
    ) -> str:
        quest = get_current_quest(context)

        if not quest:
            return self.log_error(
                "You weren't currently in a quest.",
            )

        generator = get_story_text_generator(context)

        player = game_state.player

        # Let's do some things to tidy up.
        task = generator.generate(
            text=f"What object or item did {player.name} find during that story? It should fit the setting of the story and help {player.motivation} achieve their goal. Please respond only with ITEM NAME: <name> ITEM DESCRIPTION: <description>"
        )
        task.wait()
        response = task.output.blocks[0].text

        item = Item()
        parts = response.split("ITEM DESCRIPTION:")
        if len(parts) == 2:
            item.name = parts[0].replace("ITEM NAME:", "").strip()
            item.description = parts[1].strip()
        else:
            item.name = response.strip()

        if item.name:
            quest.new_items = [item]

        if not player.inventory:
            player.inventory = []
        player.inventory.append(item)

        # Increase the player's rank
        player.rank += quest.rank_delta
        player.gold += quest.gold_delta

        summary = (
            # TODO: This is stateless.
            generator.generate(
                text="Summarize this quest in three sentences.",
                options={"max_tokens": 200},
            )
            .wait()
            .blocks[0]
            .text
        )
        quest.text_summary = summary

        # Finally.. close the quest.
        game_state.current_quest = None

        # TODO: Verify that python's pass-by-reference means all the above modifications are automatically
        # included in this.
        save_game_state(game_state, context)

        # This notifies the web UI that it is time to transition back to Camp
        send_agent_status_message(AgentStatusMessageTag.QUEST_COMPLETE)

        return "You've finished the quest! TODO: Stream celebration."

    def run(
        self, tool_input: List[Block], context: AgentContext
    ) -> Union[List[Block], Task[Any]]:
        game_state = get_game_state(context)
        msg = self.end_quest(game_state, context)
        return [Block(text=msg)]
