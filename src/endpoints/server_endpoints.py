import logging

from steamship import Steamship
from steamship.invocable import get, post
from steamship.invocable.package_mixin import PackageMixin

from schema.server_settings import ServerSettings
from utils.agent_service import AgentService
from utils.context_utils import get_server_settings, save_server_settings
from utils.fields import get_model_schema


class ServerSettingsMixin(PackageMixin):
    """Provides endpoints for Game State."""

    agent_service: AgentService
    client: Steamship

    def __init__(self, client: Steamship, agent_service: AgentService):
        self.client = client
        self.agent_service = agent_service

    @post("/server_settings")
    def post_server_settings(self, **kwargs) -> dict:
        """Set the server settings."""
        try:
            server_settings = ServerSettings.parse_obj(kwargs)
            context = self.agent_service.build_default_context()
            existing_state = get_server_settings(context)
            existing_state.update_from_web(server_settings)
            save_server_settings(existing_state, context)
            return server_settings.dict()
        except BaseException as e:
            logging.exception(e)
            raise e

    @get("/server_settings")
    def get_server_settings(self) -> dict:
        """Get the server settings."""
        context = self.agent_service.build_default_context()
        return get_server_settings(context).dict()

    @get("/server_settings/schema")
    def get_server_settings_schema(self) -> dict:
        model_schema = get_model_schema(ServerSettings)
        return {
            "package_name": "",
            "package_version": "",
            "model_name": "ServerSettings",
            "schema": model_schema
        }
