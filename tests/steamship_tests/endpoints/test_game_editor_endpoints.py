from typing import Callable, Optional, Tuple

import pytest
import requests
from steamship import Block, Steamship

from api import AdventureGameService
from schema.server_settings import ServerSettings


@pytest.mark.parametrize(
    "invocable_handler_with_client", [AdventureGameService], indirect=True
)
def test_generate_adventure_image_suggestion(
    invocable_handler_with_client: Tuple[
        Callable[[str, str, Optional[dict]], dict], Steamship
    ]
):
    invocable_handler, client = invocable_handler_with_client
    task_dict = invocable_handler(
        "POST", "generate_suggestion", {"field_name": "adventure_image"}
    )
    block = Block.parse_obj(task_dict.get("data"))

    url = f"{client.config.api_base}block/{block.id}/raw"
    response = requests.get(url)
    assert response.ok


@pytest.mark.parametrize(
    "invocable_handler_with_client", [AdventureGameService], indirect=True
)
def test_generate_preview(
    invocable_handler_with_client: Tuple[
        Callable[[str, str, Optional[dict]], dict], Steamship
    ]
):
    invocable_handler, client = invocable_handler_with_client
    task_dict = invocable_handler(
        "POST", "generate_preview", {"field_name": "camp_image"}
    )
    block = Block.parse_obj(task_dict.get("data"))
    url = f"{client.config.api_base}block/{block.id}/raw"
    response = requests.get(url)
    assert response.ok


@pytest.mark.parametrize(
    "invocable_handler_with_client", [AdventureGameService], indirect=True
)
def test_generate_profile_image_preview(
    invocable_handler_with_client: Tuple[
        Callable[[str, str, Optional[dict]], dict], Steamship
    ]
):
    payload = {
        "field_name": "profile_image",
        "field_key_path": ["profile-divider"],
        "unsaved_server_settings": {
            "profile_image_theme": "dall_e_2_neon_cyberpunk",
        },
    }
    invocable_handler, client = invocable_handler_with_client

    task_dict = invocable_handler("POST", "generate_preview", payload)
    block = Block.parse_obj(task_dict.get("data"))
    url = f"{client.config.api_base}block/{block.id}/raw"
    response = requests.get(url)
    assert response.ok


@pytest.mark.parametrize(
    "invocable_handler_with_client", [AdventureGameService], indirect=True
)
def test_generate_suggestion(
    invocable_handler_with_client: Tuple[
        Callable[[str, str, Optional[dict]], dict], Steamship
    ]
):
    invocable_handler, client = invocable_handler_with_client
    task_dict = invocable_handler(
        "POST", "generate_suggestion", {"field_name": "narrative_voice"}
    )
    block = Block.parse_obj(task_dict.get("data"))
    url = f"{client.config.api_base}block/{block.id}/raw"
    response = requests.get(url)
    assert response.ok


@pytest.mark.parametrize(
    "invocable_handler_with_client", [AdventureGameService], indirect=True
)
def test_generate_suggestion_adventure_name(
    invocable_handler_with_client: Tuple[
        Callable[[str, str, Optional[dict]], dict], Steamship
    ]
):
    invocable_handler, client = invocable_handler_with_client
    task_dict = invocable_handler("POST", "generate_suggestion", {"field_name": "name"})
    block = Block.parse_obj(task_dict.get("data"))
    url = f"{client.config.api_base}block/{block.id}/raw"
    response = requests.get(url)
    assert response.ok


@pytest.mark.parametrize(
    "invocable_handler_with_client", [AdventureGameService], indirect=True
)
def test_generate_character_suggestion(
    invocable_handler_with_client: Tuple[
        Callable[[str, str, Optional[dict]], dict], Steamship
    ]
):
    invocable_handler, client = invocable_handler_with_client
    task_dict = invocable_handler(
        "POST",
        "generate_suggestion",
        {"field_name": "name", "field_key_path": ["characters", 0, "name"]},
    )
    block = Block.parse_obj(task_dict.get("data"))
    if block.text:
        print(block.text)
        return

    url = f"{client.config.api_base}block/{block.id}/raw"
    response = requests.get(url)
    assert response.ok


@pytest.mark.parametrize(
    "invocable_handler_with_client", [AdventureGameService], indirect=True
)
def test_generate_character_image_suggestion(
    invocable_handler_with_client: Tuple[
        Callable[[str, str, Optional[dict]], dict], Steamship
    ]
):
    invocable_handler, client = invocable_handler_with_client
    task_dict = invocable_handler(
        "POST",
        "generate_suggestion",
        {"field_name": "name", "field_key_path": ["characters", 0, "image"]},
    )
    block = Block.parse_obj(task_dict.get("data"))

    url = f"{client.config.api_base}block/{block.id}/raw"
    response = requests.get(url)
    assert response.ok


@pytest.mark.parametrize(
    "invocable_handler_with_client", [AdventureGameService], indirect=True
)
def test_generate_suggestion_with_save(
    invocable_handler_with_client: Tuple[
        Callable[[str, str, Optional[dict]], dict], Steamship
    ]
):
    invocable_handler, client = invocable_handler_with_client

    ss1: ServerSettings = ServerSettings.parse_obj(
        invocable_handler("GET", "server_settings", {}).get("data")
    )

    task_dict = invocable_handler(
        "POST",
        "generate_suggestion",
        {
            "field_name": "narrative_voice",
            "save_result": True,
            "field_key_path": ["narrative_voice"],
        },
    )

    ss2: ServerSettings = ServerSettings.parse_obj(
        invocable_handler("GET", "server_settings", {}).get("data")
    )

    assert ss1.narrative_voice is None
    assert ss1.narrative_voice != ""

    assert ss2.narrative_voice is not None
    assert ss2.narrative_voice != ""

    assert ss1.narrative_voice != ss2.narrative_voice

    block = Block.parse_obj(task_dict.get("data"))
    url = f"{client.config.api_base}block/{block.id}/raw"
    response = requests.get(url)
    assert response.ok
