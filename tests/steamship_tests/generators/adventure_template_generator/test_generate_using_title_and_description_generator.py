from typing import Callable, Optional, Tuple
from unittest.mock import patch

import pytest
from steamship import Steamship
from steamship.agents.schema import AgentContext
from steamship_tests.generators.adventure_template_generator.test_generate_using_title_and_story_generator import (
    no_cache_get_server_settings,
)
from steamship_tests.utils.fake_agent_service import FakeAgentService

from api import AdventureGameService
from generators.server_settings_generators.generate_using_reddit_post_generator import (
    GenerateUsingRedditPostGenerator,
)
from schema.server_settings import ServerSettings
from utils.context_utils import get_server_settings, save_server_settings


@pytest.mark.parametrize(
    "invocable_handler_with_client", [AdventureGameService], indirect=True
)
@patch(
    "endpoints.server_endpoints.get_server_settings",
    no_cache_get_server_settings,
    create=True,
)
@patch(
    "generators.server_settings_generator.get_server_settings",
    no_cache_get_server_settings,
    create=True,
)
@patch(
    "generators.editor_suggestion_generator.get_server_settings",
    no_cache_get_server_settings,
    create=True,
)
def test_generate_using_title_and_description_generator(
    invocable_handler_with_client: Tuple[
        Callable[[str, str, Optional[dict]], dict], Steamship
    ]
):
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

    generator = GenerateUsingRedditPostGenerator()

    task = generator.generate(service, context, {})
    # This will contain the server_settings
    print(task.output)

    server_settings: ServerSettings = ServerSettings.parse_obj(
        invocable_handler("GET", "server_settings", {}).get("data")
    )
    assert server_settings.source_url == the_url
    assert server_settings.name == "Unplanned Outing"
    assert "Claire" in server_settings.description
