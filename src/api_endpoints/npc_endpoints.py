from steamship import Steamship
from steamship.agents.service.agent_service import AgentService
from steamship.invocable import post
from steamship.invocable.package_mixin import PackageMixin

from tools.end_conversation_tool import EndConversationTool
from tools.start_conversation_tool import StartConversationTool

# An instnace is a game instance.
from utils.context_utils import get_game_state


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
        game_state = get_game_state(context)
        tool = StartConversationTool()
        convo_or_error = tool.start_conversation(character_name, game_state, context)
        if isinstance(convo_or_error, str):
            return {"error": True, "message": convo_or_error}
        return convo_or_error.dict()

    @post("/end_conversation")
    def end_conversation(self, **kwargs) -> dict:
        """Starts a conversation with the NPC by the provided name."""
        context = self.agent_service.build_default_context()
        game_state = get_game_state(context)
        tool = EndConversationTool()
        response = tool.end_conversation(game_state, context)
        return {"message": response}
