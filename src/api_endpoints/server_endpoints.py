from steamship import Steamship
from steamship.invocable import get, post
from steamship.invocable.package_mixin import PackageMixin


class ServerSettingsMixin(PackageMixin):
    """Provides endpoints for User Settings."""

    client: Steamship

    def __init__(self, client: Steamship):
        self.client = client

    @post("/server_settings")
    def post_game_state(self, **kwargs) -> dict:
        """Set the user settings."""
        # TODO: Save the user settings
        return {}

    @get("/server_settings")
    def get_game_state(self, **kwargs) -> dict:
        """Get the user settings."""
        # TODO: Load the user settings
        return {}
