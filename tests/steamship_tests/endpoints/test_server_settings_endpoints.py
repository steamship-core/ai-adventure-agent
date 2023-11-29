import pathlib
from typing import Callable, Optional

import pytest
import yaml

from api import AdventureGameService
from schema.server_settings import ServerSettings


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


@pytest.mark.parametrize("invocable_handler", [AdventureGameService], indirect=True)
def test_server_settings_endpoint_update(
    invocable_handler: Callable[[str, str, Optional[dict]], dict]
):
    ss0: ServerSettings = ServerSettings.parse_obj(
        invocable_handler("GET", "server_settings", {}).get("data")
    )
    assert ss0
    assert ss0.adventure_goal

    ss1: ServerSettings = ServerSettings.parse_obj(ss0.dict())
    ss1.adventure_goal = "HI HI"

    invocable_handler("POST", "server_settings", ss1.dict())

    ss2: ServerSettings = ServerSettings.parse_obj(
        invocable_handler("GET", "server_settings", {}).get("data")
    )

    assert ss2.adventure_goal == ss1.adventure_goal
    assert ss2.adventure_goal != ss0.adventure_goal

    invocable_handler(
        "POST", "patch_server_settings", {"adventure_background": "BAR BAR"}
    )

    ss3: ServerSettings = ServerSettings.parse_obj(
        invocable_handler("GET", "server_settings", {}).get("data")
    )

    # We're checking here that the partial update DID NOT REVERT
    assert ss3.adventure_goal == ss1.adventure_goal
    assert ss3.adventure_goal != ss0.adventure_goal
    assert ss3.adventure_background == "BAR BAR"


@pytest.mark.parametrize("invocable_handler", [AdventureGameService], indirect=True)
def test_server_settings_generate_preview(
    invocable_handler: Callable[[str, str, Optional[dict]], dict]
):
    basepath = pathlib.Path(__file__).parent.resolve()
    with open(basepath / "../../../example_content/image_theme.yaml") as file:
        ss: ServerSettings = ServerSettings.parse_obj(yaml.safe_load(file.read()))
        for theme in ss.image_themes:
            assert hasattr(theme, "name")

        full_preview_dict = {
            "field_name": "profile_image",
            "unsaved_server_settings": ss.dict(),
        }

        resp = invocable_handler("POST", "generate_preview", full_preview_dict)
        assert resp.get("http") is not None
        http = resp.get("http")
        assert http.get("status") is not None
        status = http.get("status")
        assert status == 200
