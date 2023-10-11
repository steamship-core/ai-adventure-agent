from typing import Callable, Optional

import pytest

from api import AdventureGameService


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
