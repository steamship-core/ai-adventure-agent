import logging
from typing import Callable, Optional, Tuple
from unittest.mock import patch

import pytest
from steamship import Steamship, Task
from steamship.agents.schema import AgentContext
from steamship.utils.kv_store import KeyValueStore
from steamship_tests.utils.fake_agent_service import FakeAgentService

from api import AdventureGameService
from generators.server_settings_generators.generate_using_reddit_post_generator import (
    GenerateUsingRedditPostGenerator,
)
from generators.server_settings_generators.generate_using_title_and_description_generator import (
    GenerateUsingTitleAndDescriptionGenerator,
)
from schema.server_settings import ServerSettings
from utils.agent_service import AgentService
from utils.context_utils import (
    _SERVER_SETTINGS_KEY,
    get_server_settings,
    save_server_settings,
)


def inner_generate(
    self,
    agent_service: AgentService,
    context: AgentContext,
    wait_on_task: Task = None,
    generation_config: Optional[dict] = None,
):
    return wait_on_task


def no_cache_get_server_settings(
    context: AgentContext,
) -> "ServerSettings":  # noqa: F821

    # Get it from the KV Store
    kv = KeyValueStore(context.client, _SERVER_SETTINGS_KEY)
    value = kv.get(_SERVER_SETTINGS_KEY)

    if value:
        logging.debug(f"Parsing Server Settings from stored value: {value}")
        server_settings = ServerSettings.parse_obj(value)
    else:
        logging.debug("Creating new Server Settings -- one didn't exist!")
        server_settings = ServerSettings()

    return server_settings


@pytest.mark.parametrize(
    "invocable_handler_with_client", [AdventureGameService], indirect=True
)
@patch("utils.context_utils.get_server_settings", no_cache_get_server_settings)
@patch.object(
    GenerateUsingTitleAndDescriptionGenerator, "inner_generate", inner_generate
)
def test_generate_using_title_and_story(
    invocable_handler_with_client: Tuple[
        Callable[[str, str, Optional[dict]], dict], Steamship
    ]
):
    generator = GenerateUsingRedditPostGenerator()

    invocable_handler, client = invocable_handler_with_client
    context = AgentContext.get_or_create(
        client=client, context_keys={"id": "testing-foo"}, searchable=False
    )

    the_url = (
        "https://www.reddit.com/r/shortstories/comments/18521s3/mf_unplanned_outing/"
    )
    service = FakeAgentService(handler=invocable_handler, client=client)

    server_settings = get_server_settings(context)
    server_settings.source_url = the_url
    save_server_settings(server_settings, context)

    task = generator.generate(service, context, {})
    # This will contain the server_settings
    print(task.output)

    server_settings = get_server_settings(context)
    assert server_settings.source_url == the_url
    assert server_settings.name == "Unplanned Outing"
    assert "Claire Fuller" in server_settings.source_story_text
