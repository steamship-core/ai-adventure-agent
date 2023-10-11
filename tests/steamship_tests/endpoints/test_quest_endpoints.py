from typing import Callable, Optional

import pytest
from steamship import Task, TaskState

from api import AdventureGameService
from schema.game_state import GameState
from schema.quest import Quest
from schema.server_settings import ServerSettings


@pytest.mark.parametrize("invocable_handler", [AdventureGameService], indirect=True)
def test_going_on_quest_consumes_energy(
    invocable_handler: Callable[[str, str, Optional[dict]], dict]
):
    ENERGY = 1000

    invocable_handler("POST", "game_state", {"player": {"energy": ENERGY}})
    gs = GameState.parse_obj(invocable_handler("GET", "game_state", {}).get("data"))
    assert gs.player.energy == ENERGY

    result = invocable_handler("POST", "start_quest", {})
    quest: Quest = Quest.parse_obj(result.get("data"))

    assert quest

    server_settings = ServerSettings()
    assert server_settings.quest_cost > 0

    # The cost of the quest is equal to the server settings
    assert quest.energy_delta == server_settings.quest_cost

    # Now end the quest
    invocable_handler("POST", "end_quest", {})

    gs_after_quest = GameState.parse_obj(
        invocable_handler("GET", "game_state", {}).get("data")
    )
    assert gs_after_quest.player.energy == gs.player.energy - server_settings.quest_cost


@pytest.mark.parametrize("invocable_handler", [AdventureGameService], indirect=True)
def test_going_on_quest_impossible_if_insufficient_energy(
    invocable_handler: Callable[[str, str, Optional[dict]], dict]
):
    server_settings = ServerSettings()
    assert server_settings.quest_cost > 0

    # Not enough energy!
    ENERGY = server_settings.quest_cost - 1
    invocable_handler("POST", "game_state", {"player": {"energy": ENERGY}})
    gs = GameState.parse_obj(invocable_handler("GET", "game_state", {}).get("data"))
    assert gs.player.energy == ENERGY

    # Now try to start a quest
    result = invocable_handler("POST", "start_quest", {})
    assert result.get("data") is None

    task = Task.parse_obj(result.get("status"))
    assert task.state == TaskState.failed
    assert f"{gs.player.energy}" in task.status_message
