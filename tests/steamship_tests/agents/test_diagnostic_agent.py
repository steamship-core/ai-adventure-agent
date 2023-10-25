from typing import Callable, Optional

import pytest

from agents.diagnostic_agent import DiagnosticMode
from api import AdventureGameService
from schema.game_state import GameState


@pytest.mark.parametrize("invocable_handler", [AdventureGameService], indirect=True)
def test_knock_knock(invocable_handler: Callable[[str, str, Optional[dict]], dict]):
    diagnostic_mode = DiagnosticMode.KNOCK_KNOCK
    gs: GameState = GameState.parse_obj(
        invocable_handler("GET", "game_state", {}).get("data")
    )
    gs.diagnostic_mode = diagnostic_mode
    invocable_handler("POST", "game_state", gs.dict())

    # Invoke
    resp = invocable_handler("POST", "prompt", {"prompt": "Hi"})

    # Assert that we ran the right test
    blocks = resp.get("data")
    assert blocks[-1].get("text") == diagnostic_mode.value
