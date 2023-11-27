from typing import List, Optional

from steamship import Task
from steamship.utils.url import Verb

from api import AdventureGameService


class FakeAgentService(AdventureGameService):
    def __init__(self, handler, **kwargs):
        self.handler = handler
        super().__init__(**kwargs)

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

        response_dict = self.handler(verb, method, arguments)
        return Task(output=response_dict)
