from typing import Optional

from steamship import Steamship
from steamship.agents.service.agent_service import AgentService
from steamship.invocable import post
from steamship.invocable.package_mixin import PackageMixin

# An instnace is a game instance.
from context_utils import get_user_settings
from tools.start_quest_tool import StartQuestTool


class QuestMixin(PackageMixin):
    """Provides endpoints for User Settings."""

    client: Steamship
    agent_service: AgentService

    def __init__(self, client: Steamship, agent_service: AgentService):
        self.client = client
        self.agent_service = agent_service

    @post("/start_quest")
    def start_quest(self, purpose: Optional[str] = None, **kwargs) -> dict:
        """Starts a quest.
        THOUGHT: Can this call into some functionality (agent/tool) which could also be performed by a Function calling agent?
        """
        context = self.agent_service.build_default_context()
        user_settings = get_user_settings(context)
        quest_tool = StartQuestTool()
        quest = quest_tool.start_quest(user_settings, context, purpose)
        return quest.dict()
