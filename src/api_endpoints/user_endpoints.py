from steamship import Steamship
from steamship.agents.service.agent_service import AgentService
from steamship.invocable import get, post
from steamship.invocable.package_mixin import PackageMixin

from schema.game_state import GameState

# An instnace is a game instance.
from utils.context_utils import save_game_state


class GameStateMixin(PackageMixin):
    """Provides endpoints for User Settings."""

    agent_service: AgentService
    client: Steamship

    def __init__(self, client: Steamship, agent_service: AgentService):
        self.client = client
        self.agent_service = agent_service

    @post("/game_state")
    def post_game_state(self, **kwargs) -> dict:
        """Set the user settings."""
        game_state = GameState.parse_obj(kwargs)
        context = self.agent_service.build_default_context()
        # TODO: Do we want to update more softly rather than completely replace? That's pretty harsh.
        save_game_state(game_state, context)
        return game_state.dict()

    @get("/game_state")
    def get_game_state(self) -> dict:
        """Get the user settings."""
        return GameState.load(client=self.client).dict()
