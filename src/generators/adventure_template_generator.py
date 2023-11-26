import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Union

from pydantic.main import BaseModel
from steamship import Task
from steamship.agents.schema import AgentContext
from steamship.utils.url import Verb

from schema.server_settings import ServerSettings
from utils.agent_service import AgentService
from utils.context_utils import get_server_settings, save_server_settings


class AdventureTemplateGenerator(BaseModel, ABC):
    """Generates an ENTIRE configuration -- multiple fields -- in a dict file."""

    @abstractmethod
    def inner_generate(
        self, agent_service: AgentService, context: AgentContext
    ) -> Task:
        pass

    @abstractmethod
    def generate(
        self,
        agent_service: AgentService,
        context: AgentContext,
        unsaved_server_settings: Optional[dict] = None,
    ) -> Task:
        """Generate an entire Adventure Template."""
        self.save_unsaved_server_settings(agent_service, unsaved_server_settings)

        last_task = self.inner_generate(agent_service, context)

        # Schedule the clearing of the generation_task_id value
        wait_on_tasks = [last_task] if last_task else []
        return_task = (
            generation_complete_task
        ) = self.schedule_record_generation_complete(wait_on_tasks, agent_service)

        # Mark that we're in the state of generating
        self.record_generation_started(generation_complete_task, context)

        return return_task

    def save_unsaved_server_settings(
        self,
        agent_service: AgentService,
        unsaved_server_settings: Optional[dict] = None,
    ):
        """Before we begin generating, we save all the unsaved settings."""

        if unsaved_server_settings is not None:
            logging.info(
                "Updating the server settings to generate the suggestion. This should only be done on the development agent."
            )
            try:
                server_settings = ServerSettings.parse_obj(unsaved_server_settings)
                context = agent_service.build_default_context()
                existing_state = get_server_settings(context)
                existing_state.update_from_web(server_settings)
                save_server_settings(existing_state, context)
            except BaseException as e:
                logging.exception(e)
                raise e

    def schedule_generation(
        self,
        field_name: str,
        field_key_path: List[Union[str, int]],
        wait_on_tasks: Optional[List[Task]],
        agent_service: AgentService,
    ) -> Task:
        return agent_service.invoke_later(
            method="/generate_suggestion",
            verb=Verb.POST,
            wait_on_tasks=wait_on_tasks,
            arguments={
                "field_name": field_name,
                "field_key_path": field_key_path,
                "save_to_adventure_template": True,
            },
        )

    def record_generation_started(
        self, completion_task: Task, context: AgentContext
    ) -> Task:
        server_settings = get_server_settings(context)
        server_settings.generation_task_id = completion_task.task_id
        save_server_settings(server_settings, context)
        return completion_task

    def schedule_record_generation_complete(
        self, wait_on_tasks: Optional[List[Task]], agent_service: AgentService
    ) -> Task:
        return agent_service.invoke_later(
            method="/server_settings",
            verb=Verb.POST,
            wait_on_tasks=wait_on_tasks,
            arguments={"generation_task_id": ""},
        )
