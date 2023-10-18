from typing import Callable, Optional

import pytest

from api import AdventureGameService


@pytest.mark.parametrize("invocable_handler", [AdventureGameService], indirect=True)
def test_get_server_settings(
    invocable_handler: Callable[[str, str, Optional[dict]], dict]
):
    gs = invocable_handler("GET", "server_settings", {})
    assert gs


@pytest.mark.parametrize("invocable_handler", [AdventureGameService], indirect=True)
def test_server_settings_endpoint(
    invocable_handler: Callable[[str, str, Optional[dict]], dict]
):
    gs = invocable_handler("GET", "server_settings", {})
    assert gs

    server_settings = gs.get("data")
    assert server_settings

    server_settings["default_story_model"] = "BOO"
    invocable_handler("POST", "server_settings", server_settings)

    gs2 = invocable_handler("GET", "server_settings", {})
    assert gs2
    server_settings2 = gs2.get("data")

    assert server_settings2.get("default_story_model") == "BOO"
