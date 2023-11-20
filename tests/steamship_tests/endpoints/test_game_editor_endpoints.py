from typing import Callable, Optional, Tuple

import pytest
import requests
from steamship import Block, Steamship

from api import AdventureGameService


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
