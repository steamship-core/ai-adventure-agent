import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Union

from pydantic.main import BaseModel
from steamship import Task
from steamship.agents.schema import AgentContext
from steamship.utils.url import Verb

from utils.agent_service import AgentService
from utils.context_utils import get_server_settings, save_server_settings


class ServerSettingsGenerator(BaseModel, ABC):
    """Generates an ENTIRE configuration -- multiple fields -- in a dict file."""

    @abstractmethod
    def inner_generate(
        self,
        agent_service: AgentService,
        context: AgentContext,
        wait_on_task: Task = None,
    ) -> Task:
        pass

    def generate(
        self,
        agent_service: AgentService,
        context: AgentContext,
        unsaved_server_settings: Optional[dict] = None,
        wait_on_task: Task = None,
    ) -> Task:
        """Generate an entire Adventure Template."""
        self.save_unsaved_server_settings(agent_service, unsaved_server_settings)

        last_task = self.inner_generate(
            agent_service, context, wait_on_task=wait_on_task
        )

        # Schedule the clearing of the generation_task_id value
        wait_on_tasks = [last_task] if last_task else []
        logging.info(f"Will await on final generation task: {wait_on_tasks}")
        generation_complete_task = self.schedule_record_generation_complete(
            wait_on_tasks, agent_service
        )

        # Mark that we're in the state of generating
        self.record_generation_started(generation_complete_task, context)

        return generation_complete_task

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
                # NOTE: We can't use update_from_web because that will BLAST OVER the things not in unsaved_server_settings
                # with the Pydantic defaults!
                context = agent_service.build_default_context()
                server_settings = get_server_settings(context)
                for k, v in unsaved_server_settings.items():
                    setattr(server_settings, k, v)
                save_server_settings(server_settings, context)
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
                "save_to_server_settings": True,
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
            method="/patch_server_settings",
            verb=Verb.POST,
            wait_on_tasks=wait_on_tasks,
            arguments={"generation_task_id": ""},
        )
