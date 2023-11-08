from typing import Callable, Optional, Tuple

import pytest
from steamship import Steamship
from steamship.agents.schema import AgentContext

from api import AdventureGameService
from schema.game_state import GameState
from utils.context_utils import save_game_state


@pytest.mark.parametrize(
    "invocable_handler_with_client", [AdventureGameService], indirect=True
)
def test_induce_error(
    invocable_handler_with_client: Tuple[
        Callable[[str, str, Optional[dict]], dict], Steamship
    ]
):
    invocable_handler, client = invocable_handler_with_client
    context = AgentContext.get_or_create(client, context_keys={"_id": "doo"})

    # Now attempt to onboard!
    gs: GameState = GameState.parse_obj(
        invocable_handler("GET", "game_state", {}).get("data")
    )
    gs.player.description = "A tomato"
    gs.player.background = "From the farm"
    gs.player.name = "Tomatokins"
    gs.diagnostic_mode = (
        "setting this will cause the complete onboarding step to throw an exception"
    )

    save_game_state(gs, context)

    # Now we attempt to complete onboarding
    invocable_handler("POST", "complete_onboarding", {})

    # Now we get the game state and see that it's an error!

    gs2: GameState = GameState.parse_obj(
        invocable_handler("GET", "game_state", {}).get("data")
    )
    assert gs2.unrecoverable_error is not None
    assert gs2.active_mode == "error"
