from typing import Callable, Optional, Tuple

import pytest
from steamship import Steamship, Task, TaskState
from steamship.agents.schema import ChatHistory

from api import AdventureGameService
from schema.game_state import ActiveMode, GameState
from schema.quest import Quest
from schema.server_settings import ServerSettings

COMPLETED_ONBOARDING: GameState = GameState.parse_obj(
    {
        "tone": "Funny",
        "genre": "Comedy",
        "player": {
            "name": "Mark The QA Man",
            "description": "Has a funny shaped keyboard",
            "background": "Good at QA",
            "motivation": "To find bugs",
            "inventory": [
                {"name": "The magic keyboard", "description": "Always types bad input"}
            ],
        },
    }
)


@pytest.mark.parametrize("invocable_handler", [AdventureGameService], indirect=True)
def test_calling_start_quest_causes_active_quest(
    invocable_handler: Callable[[str, str, Optional[dict]], dict]
):

    game_state: GameState = GameState.parse_obj(
        invocable_handler("GET", "game_state", {}).get("data")
    )
    assert game_state.current_quest is None
    assert game_state.active_mode == ActiveMode.ONBOARDING.value

    invocable_handler("POST", "game_state", COMPLETED_ONBOARDING.dict())

    invocable_handler("POST", "complete_onboarding", {})

    start_state = invocable_handler("POST", "start_quest", {})
    assert start_state.get("data")
    quest: Quest = Quest.parse_obj(start_state.get("data"))
    assert quest.name

    game_state: GameState = GameState.parse_obj(
        invocable_handler("GET", "game_state", {}).get("data")
    )
    assert game_state.tone
    assert game_state.genre
    assert game_state.player.name
    assert game_state.player.description
    assert game_state.player.background
    assert game_state.player.motivation
    assert game_state.player.inventory

    assert game_state.tone == COMPLETED_ONBOARDING.tone
    assert game_state.genre == COMPLETED_ONBOARDING.genre
    assert game_state.player.name == COMPLETED_ONBOARDING.player.name
    assert game_state.player.description == COMPLETED_ONBOARDING.player.description
    assert game_state.player.background == COMPLETED_ONBOARDING.player.background
    assert game_state.player.motivation == COMPLETED_ONBOARDING.player.motivation
    assert game_state.player.inventory == COMPLETED_ONBOARDING.player.inventory

    assert game_state.current_quest
    assert game_state.active_mode.value == ActiveMode.QUEST.value


@pytest.mark.parametrize("invocable_handler", [AdventureGameService], indirect=True)
def test_going_on_quest_consumes_energy(
    invocable_handler: Callable[[str, str, Optional[dict]], dict]
):
    energy = 1000

    invocable_handler("POST", "game_state", {"player": {"energy": energy}})
    gs = GameState.parse_obj(invocable_handler("GET", "game_state", {}).get("data"))
    assert gs.player.energy == energy

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
    energy = server_settings.quest_cost - 1
    invocable_handler("POST", "game_state", {"player": {"energy": energy}})
    gs = GameState.parse_obj(invocable_handler("GET", "game_state", {}).get("data"))
    assert gs.player.energy == energy

    # Now try to start a quest
    result = invocable_handler("POST", "start_quest", {})
    assert result.get("data") is None

    task = Task.parse_obj(result.get("status"))
    assert task.state == TaskState.failed
    assert f"{gs.player.energy}" in task.status_message


@pytest.mark.parametrize(
    "invocable_handler_with_client", [AdventureGameService], indirect=True
)
def test_narrate_block(
    invocable_handler_with_client: Tuple[
        Callable[[str, str, Optional[dict]], dict], Steamship
    ]
):
    handler, client = invocable_handler_with_client
    history = ChatHistory.get_or_create(client, context_keys={"id": "bar"})
    block = history.append_assistant_message(text="Hello there!")

    resp = handler("POST", "narrate_block", {"block_id": block.id})

    assert resp.get("data")
    assert resp.get("data").get("url")
