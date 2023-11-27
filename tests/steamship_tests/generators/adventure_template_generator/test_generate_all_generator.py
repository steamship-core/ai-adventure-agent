from typing import Callable, List, Optional, Tuple

import pytest
from steamship import Steamship, Task
from steamship.agents.schema import AgentContext
from steamship.utils.url import Verb

from api import AdventureGameService
from generators.adventure_template_generators.generate_all_generator import (
    GenerateAllGenerator,
)
from utils.context_utils import get_adventure_template


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

    class FakeAgentService(AdventureGameService):
        def invoke_later(
            self,
            method: str,
            verb: Verb = Verb.POST,
            arguments: dict = {},
            wait_on_tasks: Optional[List[Task]] = None,
        ):
            # Note: the correct impl would inspect the fn lookup for the fn with the right verb.
            method = method.rstrip("/").lstrip("/")

            if wait_on_tasks:
                for task in wait_on_tasks:
                    if type(task) == Task and task.task_id:
                        task.wait()

            response_dict = invocable_handler(verb, method, arguments)
            return Task(output=response_dict)

    service = FakeAgentService(client=client)

    generator = GenerateAllGenerator()
    task = generator.generate(service, context, {})
    # This will contain the server_settings
    print(task.output)

    adventure_template = get_adventure_template(context)
    print(adventure_template)
