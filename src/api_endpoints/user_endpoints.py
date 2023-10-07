from steamship import Steamship
from steamship.agents.service.agent_service import AgentService
from steamship.invocable import get, post
from steamship.invocable.package_mixin import PackageMixin

# An instnace is a game instance.
from context_utils import save_user_settings
from schema.user_settings import UserSettings


class UserSettingsMixin(PackageMixin):
    """Provides endpoints for User Settings."""

    agent_service: AgentService
    client: Steamship

    def __init__(self, client: Steamship, agent_service: AgentService):
        self.client = client
        self.agent_service = agent_service

    @post("/user_settings")
    def post_user_settings(self, **kwargs) -> dict:
        """Set the user settings."""
        user_settings = UserSettings.parse_obj(kwargs)
        context = self.agent_service.build_default_context()
        # TODO: Do we want to update more softly rather than completely replace? That's pretty harsh.
        save_user_settings(user_settings, context)
        return user_settings.dict()

    @get("/user_settings")
    def get_user_settings(self) -> dict:
        """Get the user settings."""
        return UserSettings.load(client=self.client).dict()
