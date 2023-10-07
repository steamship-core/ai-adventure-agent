from steamship import Steamship
from steamship.agents.service.agent_service import AgentService
from steamship.invocable import post
from steamship.invocable.package_mixin import PackageMixin

# An instnace is a game instance.
from context_utils import get_user_settings
from tools.end_conversation_tool import EndConversationTool
from tools.start_conversation_tool import StartConversationTool


class NpcMixin(PackageMixin):
    """Provides endpoints for NPC Transitions."""

    client: Steamship
    agent_service: AgentService

    def __init__(self, client: Steamship, agent_service: AgentService):
        self.client = client
        self.agent_service = agent_service

    @post("/start_conversation")
    def start_conversation(self, character_name: str, **kwargs) -> dict:
        """Starts a conversation with the NPC by the provided name."""
        context = self.agent_service.build_default_context()
        user_settings = get_user_settings(context)
        tool = StartConversationTool()
        convo_or_error = tool.start_conversation(character_name, user_settings, context)
        if isinstance(convo_or_error, str):
            return {"error": True, "message": convo_or_error}
        return convo_or_error.dict()

    @post("/end_conversation")
    def end_conversation(self, **kwargs) -> dict:
        """Starts a conversation with the NPC by the provided name."""
        context = self.agent_service.build_default_context()
        user_settings = get_user_settings(context)
        tool = EndConversationTool()
        response = tool.end_conversation(user_settings, context)
        return {"message": response}
