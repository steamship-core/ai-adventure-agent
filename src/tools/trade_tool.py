from typing import Any, List, Optional, Union

from steamship import Block, SteamshipError, Task
from steamship.agents.schema import AgentContext, Tool

from schema.characters import Character, HumanCharacter
from schema.game_state import GameState
from schema.objects import TradeResult
from utils.context_utils import save_game_state


class TradeTool(Tool):
    """Attempts to perform a trade between the player and another character."""

    counter_party: Character

    def __init__(self, **kwargs):
        kwargs["name"] = "TradeTool"
        kwargs["agent_description"] = "Never use this tool."
        kwargs[
            "human_description"
        ] = "Tool to perform a trade. Do not use this tool. It's being wrapped in the Tool class only in support of eventual multi-argument tool invocation."
        kwargs["is_final"] = True
        super().__init__(**kwargs)

    def attempt_trade(  # noqa: C901
        self,
        game_state: GameState,
        context: AgentContext,
        player_seeks_to_sell: Optional[List[str]],
        player_seeks_to_buy: Optional[List[str]],
    ) -> TradeResult:

        player: HumanCharacter = game_state.player

        player_seeks_to_sell_items = player.fetch_inventory(player_seeks_to_sell or [])
        player_seeks_to_buy_items = self.counter_party.fetch_inventory(
            player_seeks_to_buy or []
        )

        player_gold = player.gold or 0
        player_sales_proceeds = (
            sum([item.price() for item in player_seeks_to_sell_items]) or 0
        )

        total_cost = sum([item.price() for item in player_seeks_to_buy_items])
        player_purchasing_power = player_gold + player_sales_proceeds

        if player_purchasing_power < total_cost:
            # We can't afford it!
            return TradeResult(
                player_name=player.name,
                player_gold=player.gold,
                player_gold_delta=0,
                counterparty_name=self.counter_party.name,
                error_message=f"You're {total_cost - player_purchasing_power} Gold short on that trade.",
            )

        # Calculate the change in gold
        gold_delta = int((-1 * total_cost) + player_sales_proceeds)

        player.inventory = [
            item
            for item in player.inventory or []
            if item not in player_seeks_to_sell_items
        ]
        self.counter_party.inventory = [
            item
            for item in self.counter_party.inventory or []
            if item not in player_seeks_to_buy_items
        ]
        player.gold = player.gold + gold_delta

        # Save the game state. The above modifications were all linked by-reference
        save_game_state(game_state, context)

        return TradeResult(
            player_name=player.name,
            player_gold=player.gold,
            player_gold_delta=gold_delta,
            player_bought=player_seeks_to_buy_items,
            player_sold=player_seeks_to_sell_items,
            player_inventory=player.inventory,
            counterparty_name=self.counter_party.name,
        )

    def run(
        self, tool_input: List[Block], context: AgentContext
    ) -> Union[List[Block], Task[Any]]:
        raise SteamshipError(
            message="The TradeTool can't yet be used by an LLM. It is only invoked by the web api."
        )
