from typing import Callable, Optional

import pytest
from steamship import Steamship

from api import AdventureGameService
from schema.characters import Merchant
from schema.game_state import GameState
from schema.objects import Item, TradeResult
from tests.steamship_tests.utils.test_generation_utils import prepare_state
from tools.trade_tool import TradeTool


def get_merchant(gs: GameState) -> Optional[Merchant]:
    for npc in gs.camp.npcs:
        if npc.category == "merchant":
            return npc
    return None


@pytest.mark.parametrize("invocable_handler", [AdventureGameService], indirect=True)
def test_trade_endpoint_buy(
    invocable_handler: Callable[[str, str, Optional[dict]], dict]
):
    GOLD = 1000

    # Bring us to 1000 gold
    invocable_handler("POST", "game_state", {"player": {"gold": GOLD}})

    # Get the merchant
    gs = GameState.parse_obj(invocable_handler("GET", "game_state", {}).get("data"))

    assert gs.player.gold == GOLD

    merchant = get_merchant(gs)
    assert merchant
    assert merchant.inventory

    to_buy = [merchant.inventory[0].name]

    result = invocable_handler(
        "POST", "trade", {"counter_party": merchant.name, "buy": to_buy, "sell": []}
    )

    result = TradeResult.parse_obj(result.get("data"))

    assert result.player_gold_delta == -1 * merchant.inventory[0].price()
    assert result.player_gold == GOLD - merchant.inventory[0].price()
    assert result.player_bought
    assert result.player_bought[0] == merchant.inventory[0]


def test_trade_tool_buy():
    with Steamship.temporary_workspace() as client:
        context, game_state = prepare_state(client)
        GOLD = 1000
        game_state.player.gold = GOLD

        merchant = get_merchant(game_state)
        assert merchant
        assert merchant.inventory

        to_buy_item = merchant.inventory[0]
        to_buy = [to_buy_item.name]

        result = TradeTool(counter_party=merchant).attempt_trade(game_state, context, [], to_buy)

        assert result.player_gold_delta == -1 * to_buy_item.price()
        assert result.player_gold == GOLD - to_buy_item.price()
        assert result.player_bought
        assert result.player_bought[0] == to_buy_item

        assert game_state.player.inventory[0] == to_buy_item

@pytest.mark.parametrize("invocable_handler", [AdventureGameService], indirect=True)
def test_trade_endpoint_sell(
    invocable_handler: Callable[[str, str, Optional[dict]], dict]
):
    GOLD = 1000

    # Bring us to 1000 gold
    invocable_handler("POST", "game_state", {"player": {"gold": GOLD}})
    invocable_handler(
        "POST", "game_state", {"player": {"inventory": [{"name": "A Bandana"}]}}
    )

    # Get the merchant
    gs = GameState.parse_obj(invocable_handler("GET", "game_state", {}).get("data"))

    assert gs.player.gold == GOLD
    assert len(gs.player.inventory) == 1

    bandana: Item = gs.player.inventory[0]

    merchant = get_merchant(gs)
    assert merchant
    assert merchant.inventory

    to_buy = []
    to_sell = [bandana.name]

    result = invocable_handler(
        "POST",
        "trade",
        {"counter_party": merchant.name, "buy": to_buy, "sell": to_sell},
    )

    result = TradeResult.parse_obj(result.get("data"))

    assert result.player_gold_delta == bandana.price()
    assert result.player_gold == GOLD + bandana.price()
    assert len(result.player_bought) == 0
    assert len(result.player_sold) == 1
    assert result.player_sold[0] == bandana
