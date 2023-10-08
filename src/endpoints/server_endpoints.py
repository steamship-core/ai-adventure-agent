from steamship import Steamship
from steamship.invocable import get, post
from steamship.invocable.package_mixin import PackageMixin


class ServerSettingsMixin(PackageMixin):
    """Provides endpoints for Game State."""

    client: Steamship

    def __init__(self, client: Steamship):
        self.client = client

    @post("/server_settings")
    def post_game_state(self, **kwargs) -> dict:
        """Set the game state."""
        # TODO: Save the game state
        return {}

    @get("/server_settings")
    def get_game_state(self, **kwargs) -> dict:
        """Get the game state."""
        # TODO: Load the game state
        return {}
