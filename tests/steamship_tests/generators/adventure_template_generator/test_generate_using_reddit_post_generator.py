from typing import Callable, Optional, Tuple
from unittest.mock import patch

import pytest
from steamship import Steamship, Task
from steamship.agents.schema import AgentContext
from steamship_tests.utils.fake_agent_service import FakeAgentService

from api import AdventureGameService
from generators.server_settings_generators.generate_using_reddit_post_generator import (
    GenerateUsingRedditPostGenerator,
)
from generators.server_settings_generators.generate_using_title_and_story_generator import (
    GenerateUsingTitleAndStoryGenerator,
)
from utils.agent_service import AgentService
from utils.context_utils import get_server_settings, save_server_settings


def inner_generate(
    self,
    agent_service: AgentService,
    context: AgentContext,
    wait_on_task: Task = None,
    generation_config: Optional[dict] = None,
):
    return wait_on_task


@pytest.mark.parametrize(
    "invocable_handler_with_client", [AdventureGameService], indirect=True
)
def test_generate_using_reddit_posts(
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

    with patch.object(
        GenerateUsingTitleAndStoryGenerator, "inner_generate", inner_generate
    ):
        generator = GenerateUsingRedditPostGenerator()

        task = generator.generate(service, context, {})
        # This will contain the server_settings
        print(task.output)

        server_settings = get_server_settings(context)
        assert server_settings.source_url == the_url
        assert server_settings.name == "Unplanned Outing"
        assert "Claire Fuller" in server_settings.source_story_text
