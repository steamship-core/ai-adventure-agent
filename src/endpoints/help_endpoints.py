import json
from typing import List

from steamship import Steamship, SteamshipError
from steamship.agents.service.agent_service import AgentService
from steamship.invocable import post
from steamship.invocable.package_mixin import PackageMixin

from utils.generation_utils import generate_action_choices


class HelpMixin(PackageMixin):
    """Provides endpoints for providing help to users."""

    agent_service: AgentService
    client: Steamship

    def __init__(self, client: Steamship, agent_service: AgentService):
        self.client = client
        self.agent_service = agent_service

    @post("/generate_action_choices")
    def generate_action_choices(self, **kwargs) -> List[str]:
        """Generate (synchronously) a JSON List of multiple choice options for user actions in a quest."""
        try:
            context = self.agent_service.build_default_context()
            choices_json_block = generate_action_choices(context=context)
            choices = json.loads(choices_json_block.text)
            return choices

        except BaseException as e:
            raise SteamshipError(
                "Could not generate next action choices. Please try again.", error=e
            )
