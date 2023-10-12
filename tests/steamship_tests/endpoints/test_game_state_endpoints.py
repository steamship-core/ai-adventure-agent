from typing import Callable, Optional

import pytest
from steamship import Task, TaskState

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

    gs.player.max_energy = gs.player.energy * 2
    GameState.parse_obj(invocable_handler("POST", "game_state", gs.dict()))

    gs1: GameState = GameState.parse_obj(
        invocable_handler("GET", "game_state", {}).get("data")
    )
    assert gs1

    energy = gs1.player.energy
    max = gs1.player.max_energy

    assert energy > 0
    assert max > 0
    assert max == energy * 2

    delta = 1

    invocable_handler("POST", "add_energy", {"amount": delta})

    gs2: GameState = GameState.parse_obj(
        invocable_handler("GET", "game_state", {}).get("data")
    )
    assert gs2
    assert gs2.player.energy == energy + delta


@pytest.mark.parametrize("invocable_handler", [AdventureGameService], indirect=True)
def test_add_energy_beyond_max(
    invocable_handler: Callable[[str, str, Optional[dict]], dict]
):
    gs: GameState = GameState.parse_obj(
        invocable_handler("GET", "game_state", {}).get("data")
    )
    assert gs

    gs.player.max_energy = gs.player.energy * 2
    GameState.parse_obj(invocable_handler("POST", "game_state", gs.dict()))

    gs1: GameState = GameState.parse_obj(
        invocable_handler("GET", "game_state", {}).get("data")
    )
    assert gs1

    energy = gs1.player.energy
    max = gs1.player.max_energy

    assert energy > 0
    assert max > 0
    assert max == energy * 2

    delta = max

    invocable_handler(
        "POST", "add_energy", {"amount": delta, "fail_if_exceed_max": False}
    )

    gs2: GameState = GameState.parse_obj(
        invocable_handler("GET", "game_state", {}).get("data")
    )
    assert gs2
    assert gs2.player.energy == max

    # Now try to do it while requesting failure

    fail_response = invocable_handler("POST", "add_energy", {"amount": delta})

    assert fail_response.get("data") is None
    assert fail_response.get("status") is not None

    task = Task.parse_obj(fail_response.get("status"))

    assert task.state == TaskState.failed
    assert "exceeds" in task.status_message
