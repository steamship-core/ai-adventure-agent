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
        "POST", "generate_suggestion", {"field_name": "image"}
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
def test_generate_character_image_suggestion_dalle(
    invocable_handler_with_client: Tuple[
        Callable[[str, str, Optional[dict]], dict], Steamship
    ]
):
    invocable_handler, client = invocable_handler_with_client
    task_dict = invocable_handler(
        "POST",
        "generate_suggestion",
        {
            "field_name": "name",
            "field_key_path": ["characters", 0, "image"],
            "unsaved_server_settings": {
                "profile_image_theme": "dall_e_2_neon_cyberpunk",
                "characters": [
                    {
                        "name": "Mr. Meatball",
                        "description": "Giant friendly monster made of meatballs and cheese",
                    }
                ],
            },
        },
    )
    block = Block.parse_obj(task_dict.get("data"))

    url = f"{client.config.api_base}block/{block.id}/raw"
    response = requests.get(url)
    assert response.ok


@pytest.mark.parametrize(
    "invocable_handler_with_client", [AdventureGameService], indirect=True
)
def test_generate_character_image_suggestion_stable_diffusion(
    invocable_handler_with_client: Tuple[
        Callable[[str, str, Optional[dict]], dict], Steamship
    ]
):
    invocable_handler, client = invocable_handler_with_client
    task_dict = invocable_handler(
        "POST",
        "generate_suggestion",
        {
            "field_name": "name",
            "field_key_path": ["characters", 1, "image"],
            "unsaved_server_settings": {
                "profile_image_theme": "stable_diffusion_xl_no_loras",
                "characters": [
                    {
                        "name": "Mr. Meatball",
                        "description": "Giant friendly monster made of meatballs and cheese",
                    },
                    {
                        "name": "Mike Mechanic",
                        "description": "strong (handsome) blue-haired, always wears overalls",
                    },
                ],
            },
        },
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

    field = "adventure_background"

    task_dict = invocable_handler(
        "POST",
        "generate_suggestion",
        {
            "field_name": field,
            "save_to_server_settings": True,
            "field_key_path": [field],
        },
    )

    ss2 = invocable_handler("GET", "server_settings", {}).get("data")

    assert getattr(ss1, field) is None
    assert getattr(ss1, field) != ""

    assert field not in ss1

    assert ss2[field] is not None
    assert ss2[field] != ""

    assert getattr(ss1, field) != ss2[field]

    block = Block.parse_obj(task_dict.get("data"))
    url = f"{client.config.api_base}block/{block.id}/raw"
    response = requests.get(url)
    assert response.ok


@pytest.mark.parametrize(
    "invocable_handler_with_client", [AdventureGameService], indirect=True
)
def test_generate_second_tag_save(
    invocable_handler_with_client: Tuple[
        Callable[[str, str, Optional[dict]], dict], Steamship
    ]
):
    invocable_handler, client = invocable_handler_with_client

    field = "tags"
    idx = 2
    idx2 = 1

    invocable_handler(
        "POST",
        "generate_suggestion",
        {
            "field_name": field,
            "save_to_server_settings": True,
            "field_key_path": [field, idx],
        },
    )

    task_dict = invocable_handler(
        "POST",
        "generate_suggestion",
        {
            "field_name": field,
            "save_to_server_settings": True,
            "field_key_path": [field, idx2],
        },
    )

    ss2 = invocable_handler("GET", "server_settings", {}).get("data")

    for i in range(len(ss2[field])):
        if i in [idx, idx2]:
            assert ss2[field][i] is not None
            assert ss2[field][i] != ""
        else:
            assert ss2[field][i] is None

    block = Block.parse_obj(task_dict.get("data"))
    url = f"{client.config.api_base}block/{block.id}/raw"
    response = requests.get(url)
    assert response.ok


@pytest.mark.parametrize(
    "invocable_handler_with_client", [AdventureGameService], indirect=True
)
def test_generate_list_item_suggestion_with_save(
    invocable_handler_with_client: Tuple[
        Callable[[str, str, Optional[dict]], dict], Steamship
    ]
):
    invocable_handler, client = invocable_handler_with_client

    field = "tags"
    idx = 2

    task_dict = invocable_handler(
        "POST",
        "generate_suggestion",
        {
            "field_name": field,
            "save_to_server_settings": True,
            "field_key_path": [field, idx],
        },
    )

    ss2 = invocable_handler("GET", "server_settings", {}).get("data")

    assert ss2[field] is not None
    assert ss2[field] != ""
    assert len(ss2[field]) == idx + 1

    for i in range(len(ss2[field])):
        if i == idx:
            assert ss2[field][i] is not None
            assert ss2[field][i] != ""
        else:
            assert ss2[field][i] is None

    block = Block.parse_obj(task_dict.get("data"))
    url = f"{client.config.api_base}block/{block.id}/raw"
    response = requests.get(url)
    assert response.ok


@pytest.mark.parametrize(
    "invocable_handler_with_client", [AdventureGameService], indirect=True
)
def test_generate_list_of_objects_item_suggestion_with_save(
    invocable_handler_with_client: Tuple[
        Callable[[str, str, Optional[dict]], dict], Steamship
    ]
):
    invocable_handler, client = invocable_handler_with_client

    field = "characters"

    task_dict = invocable_handler(
        "POST",
        "generate_suggestion",
        {
            "field_name": "characters.name",
            "save_to_server_settings": True,
            "field_key_path": ["characters", 1, "name"],
        },
    )

    task_dict = invocable_handler(
        "POST",
        "generate_suggestion",
        {
            "field_name": "characters.tagline",
            "save_to_server_settings": True,
            "field_key_path": ["characters", 1, "tagline"],
        },
    )

    ss2 = invocable_handler("GET", "server_settings", {}).get("data")

    assert ss2[field] is not None
    assert ss2[field] != ""
    assert len(ss2[field]) == 2
    assert ss2[field][0].get("name") is None
    assert ss2[field][0].get("tagline") is None

    assert ss2[field][1].get("name")
    assert ss2[field][1].get("tagline")

    block = Block.parse_obj(task_dict.get("data"))
    url = f"{client.config.api_base}block/{block.id}/raw"
    response = requests.get(url)
    assert response.ok
