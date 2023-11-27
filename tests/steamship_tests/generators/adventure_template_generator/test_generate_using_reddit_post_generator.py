from typing import Callable, Optional, Tuple

import pytest
from steamship import Steamship
from steamship.agents.schema import AgentContext
from steamship_tests.utils.fake_agent_service import FakeAgentService

from api import AdventureGameService
from generators.adventure_template_generators.generate_using_reddit_post_generator import (
    GenerateUsingRedditPostGenerator,
)
from utils.context_utils import get_adventure_template, save_adventure_template


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

    service = FakeAgentService(handler=invocable_handler, client=client)

    adventure_template = get_adventure_template(context)
    adventure_template.source_url = (
        "https://www.reddit.com/r/shortstories/comments/18521s3/mf_unplanned_outing/"
    )
    save_adventure_template(adventure_template, context)

    generator = GenerateUsingRedditPostGenerator()

    task = generator.generate(service, context, {})
    # This will contain the server_settings
    print(task.output)

    adventure_template = get_adventure_template(context)
    print(adventure_template)
