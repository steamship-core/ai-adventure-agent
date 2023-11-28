from typing import Callable, Optional, Tuple

import pytest
from steamship import Steamship
from steamship.agents.schema import AgentContext
from steamship_tests.utils.fake_agent_service import FakeAgentService

from api import AdventureGameService
from generators.server_settings_generators.generate_all_generator import (
    GenerateAllGenerator,
)
from utils.context_utils import get_server_settings


@pytest.mark.parametrize(
    "invocable_handler_with_client", [AdventureGameService], indirect=True
)
def test_generate_all_endpoint(
    invocable_handler_with_client: Tuple[
        Callable[[str, str, Optional[dict]], dict], Steamship
    ]
):
    invocable_handler, client = invocable_handler_with_client
    context = AgentContext.get_or_create(
        client=client, context_keys={"id": "testing-foo"}, searchable=False
    )

    service = FakeAgentService(handler=invocable_handler, client=client)

    generator = GenerateAllGenerator()
    task = generator.generate(service, context, {})
    # This will contain the server_settings
    print(task.output)

    server_settings = get_server_settings(context)
    print(server_settings)
