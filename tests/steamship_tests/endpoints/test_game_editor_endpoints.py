from typing import Callable, Optional, Tuple, cast

import pytest
import requests
from steamship import Block, Steamship, Task

from api import AdventureGameService


@pytest.mark.parametrize(
    "invocable_handler_with_client", [AdventureGameService], indirect=True
)
def test_generate_preview_camp_image(
    invocable_handler_with_client: Tuple[
        Callable[[str, str, Optional[dict]], dict], Steamship
    ]
):
    invocable_handler, client = invocable_handler_with_client
    task_dict = invocable_handler("POST", "generate_preview_camp_image", {})
    task = Task.parse_obj(task_dict.get("data"))
    block = cast(Block, Block.parse_obj(task.output.get("blocks")[0]))
    url = f"{client.config.api_base}block/{block.id}/raw"
    response = requests.get(url)
    assert response.ok
