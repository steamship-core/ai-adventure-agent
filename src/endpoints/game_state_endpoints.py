import logging
from typing import Optional

from steamship import Steamship, SteamshipError
from steamship.agents.service.agent_service import AgentService
from steamship.invocable import get, post
from steamship.invocable.package_mixin import PackageMixin

from schema.game_state import GameState

# An instnace is a game instance.
from utils.context_utils import get_game_state, save_game_state


class GameStateMixin(PackageMixin):
    """Provides endpoints for Game State."""

    agent_service: AgentService
    client: Steamship

    def __init__(self, client: Steamship, agent_service: AgentService):
        self.client = client
        self.agent_service = agent_service

    @post("/game_state")
    def post_game_state(self, **kwargs) -> dict:
        """Set the game state."""
        try:
            game_state = GameState.parse_obj(kwargs)
            context = self.agent_service.build_default_context()
            existing_state = get_game_state(context)
            existing_state.update_from_web(game_state)
            save_game_state(existing_state, context)
            return game_state.dict()
        except BaseException as e:
            logging.exception(e)
            raise e

    @get("/game_state")
    def get_game_state(self) -> dict:
        """Get the game state."""
        context = self.agent_service.build_default_context()
        return get_game_state(context).dict()

    @post("/add_energy")
    def add_energy(
        self, amount: int, fail_if_exceed_max: Optional[bool] = True
    ) -> dict:
        """Special endpoint to add energy to a character."""
        context = self.agent_service.build_default_context()
        gs: GameState = get_game_state(context)

        if amount < 0:
            raise SteamshipError(
                message=f"Can only add a positive amount of energy. Got: {amount}"
            )

        gs.player.energy = gs.player.energy + amount
        save_game_state(gs, context)
        return gs.dict()
