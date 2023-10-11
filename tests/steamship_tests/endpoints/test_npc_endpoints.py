from typing import Callable, Optional

import pytest

from api import AdventureGameService
from schema.game_state import GameState
from schema.objects import TradeResult


@pytest.mark.parametrize("invocable_handler", [AdventureGameService], indirect=True)
def test_trade_endpoint(invocable_handler: Callable[[str, str, Optional[dict]], dict]):
    GOLD = 1000

    # Bring us to 1000 gold
    invocable_handler("POST", "game_state", {"player": {"gold": GOLD}})

    # Get the merchant
    gs = GameState.parse_obj(invocable_handler("GET", "game_state", {}).get("data"))

    assert gs.player.gold == GOLD

    assert len(gs.camp.npcs) == 2

    merchant = None
    for npc in gs.camp.npcs:
        if npc.category == "merchant":
            merchant = npc

    assert merchant.inventory
    to_buy = merchant.inventory[0].name

    result = invocable_handler(
        "POST", "trade", {"counter_party": merchant.name, "buy": [to_buy], "sell": []}
    )

    result = TradeResult.parse_obj(result.get("data"))

    assert result.player_gold_delta == merchant.inventory[0].price()
    assert result.player_gold == GOLD - merchant.inventory[0].price()
    assert result.player_bought
    assert result.player_bought[0] == merchant.inventory[0]
