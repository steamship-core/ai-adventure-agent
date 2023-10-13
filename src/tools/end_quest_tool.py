import logging
from typing import Any, List, Union

from steamship import Block, Tag, Task
from steamship.agents.logging import AgentLogging
from steamship.agents.schema import AgentContext, Tool

from schema.game_state import GameState
from schema.objects import Item
from utils.context_utils import (
    get_current_quest,
    get_game_state,
    get_image_generator,
    save_game_state,
)
from utils.generation_utils import (
    generate_quest_item,
    generate_quest_summary,
    send_agent_status_message,
)
from utils.tags import AgentStatusMessageTag, CharacterTag, TagKindExtensions


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

        get_story_text_generator(context)

        player = game_state.player

        # Let's do some things to tidy up.
        item_name, item_description = generate_quest_item(quest.name, player, context)

        item = Item()
        item.name = item_name
        item.description = item_description

        if item.name:
            quest.new_items = [item]

        if not player.inventory:
            player.inventory = []
        player.inventory.append(item)
        context.chat_history.append_system_message(
            text=player.inventory_description(),
            tags=[Tag(kind=TagKindExtensions.CHARACTER, name=CharacterTag.INVENTORY)],
        )
        save_game_state(game_state, context)

        item_image_task = None
        if svc := get_package_service(context=context):
            # async generate an image for the inventory item
            item_image_task = svc.invoke_later(
                "generate_item_image",
                arguments={
                    "item_name": item.name,
                    "item_description": item.description,
                    "context_id": _context_key_from_file(
                        key="id",
                        file=context.chat_history.file,
                    ),
                },
            )

        # Going on a quest increases the player's rank
        player.rank += quest.rank_delta

        # Going on a quest results in gold
        player.gold += quest.gold_delta

        # Going on a quest expends energy
        player.energy -= quest.energy_delta
        if player.energy < 0:
            player.energy = 0

        summary_block = generate_quest_summary(quest.name, context)
        summary = summary_block.text
        quest.text_summary = summary

        # Finally.. close the quest.
        game_state.current_quest = None

        # TODO: Verify that python's pass-by-reference means all the above modifications are automatically
        # included in this.
        save_game_state(game_state, context)

        # This notifies the web UI that it is time to transition back to Camp
        if item_image_task:
            # if there is any pending item image task, wait until it is complete.
            item_image_task.wait_until_completed()

        send_agent_status_message(AgentStatusMessageTag.QUEST_COMPLETE, context=context)

        return ""

    def run(
        self, tool_input: List[Block], context: AgentContext
    ) -> Union[List[Block], Task[Any]]:
        game_state = get_game_state(context)
        self.end_quest(game_state, context)
        return []
