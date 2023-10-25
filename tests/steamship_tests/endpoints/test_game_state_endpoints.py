from typing import Callable, Optional

import pytest

from api import AdventureGameService
from schema.game_state import GameState


@pytest.mark.parametrize("invocable_handler", [AdventureGameService], indirect=True)
def test_get_game_state(invocable_handler: Callable[[str, str, Optional[dict]], dict]):
    gs = invocable_handler("GET", "game_state", {})
    assert gs


@pytest.mark.parametrize("invocable_handler", [AdventureGameService], indirect=True)
def test_game_state_endpoint(
    invocable_handler: Callable[[str, str, Optional[dict]], dict]
):
    gs = invocable_handler("GET", "game_state", {})
    assert gs

    game_state = gs.get("data")
    assert game_state

    game_state["genre"] = "Foo"
    invocable_handler("POST", "game_state", game_state)

    gs2 = invocable_handler("GET", "game_state", {})
    assert gs2
    game_state2 = gs2.get("data")

    assert game_state2.get("genre") == "Foo"


@pytest.mark.parametrize("invocable_handler", [AdventureGameService], indirect=True)
def test_add_energy(invocable_handler: Callable[[str, str, Optional[dict]], dict]):
    gs: GameState = GameState.parse_obj(
        invocable_handler("GET", "game_state", {}).get("data")
    )
    assert gs

    GameState.parse_obj(invocable_handler("POST", "game_state", gs.dict()))

    gs1: GameState = GameState.parse_obj(
        invocable_handler("GET", "game_state", {}).get("data")
    )
    assert gs1

    energy = gs1.player.energy

    assert energy > 0

    delta = 1

    invocable_handler("POST", "add_energy", {"amount": delta})

    gs2: GameState = GameState.parse_obj(
        invocable_handler("GET", "game_state", {}).get("data")
    )
    assert gs2
    assert gs2.player.energy == energy + delta
