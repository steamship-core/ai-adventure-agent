from typing import List, Optional

from pydantic import BaseModel, Field
from steamship import Steamship, SteamshipError
from steamship.agents.llms.openai import ChatOpenAI
from steamship.agents.schema import ChatLLM
from steamship.agents.schema.agent import AgentContext

from schema.game_state import GameState
from utils.context_utils import with_function_capable_llm, with_server_settings


class ServerSettings(BaseModel):
    """Server Settings for the AI Adventure Game set by the Game Host.

    These are intended to be set by the game operator (not the user).
    """

    # Image Generation Settings
    default_profile_image_model: str = Field("dall-e", description="")
    default_background_image_model: str = Field("dall-e", description="")
    default_item_image_model: str = Field("dall-e", description="")

    # Language Generation Settings - Function calling
    default_function_capable_llm_model: str = Field("gpt-4", description="")
    default_function_capable_llm_temperature: float = Field(0.4, description="")
    default_function_capable_llm_max_tokens: int = Field(256, description="")

    # Language Generation Settings - Story telling
    default_story_model: str = Field("gpt-4", description="")
    default_story_temperature: float = Field(0.4, description="")
    default_story_max_tokens: int = Field(256, description="")

    # Narration Generation Settings
    default_narration_model: str = Field("elevenlabs", description="")

    # Narration Generation Settings
    default_background_music_model: str = Field("music-generator", description="")

    # Energy Management
    quest_cost: int = Field(10, description="The cost of going on one quest")

    def _select_model(
        self,
        allowed: List[str],
        default: Optional[str] = None,
        preferred: Optional[str] = None,
    ) -> str:
        if preferred and preferred in allowed:
            return preferred
        if default in allowed:
            return default
        raise SteamshipError(
            message=f"Invalid model selection (preferred={preferred}, default={default}). Only the following are allowed: {allowed}"
        )

    def get_function_capable_llm(self, client: Steamship) -> ChatLLM:
        """Return a plugin instance for the story generator."""
        return ChatOpenAI(client)

    def add_to_agent_context(
        self, context: AgentContext, game_state: GameState
    ) -> AgentContext:
        # TODO: This feels like a great way to interact with AgentContext, but this is a LOT of loading that has to
        # happen on EVERY call. Perhaps we move this to happen on-demand to speed things up if latency is bad.

        # User can't pick function-calling model. That's too error-prone.
        context = with_function_capable_llm(
            self.get_function_capable_llm(context.client), context
        )

        context = with_server_settings(self, context)

        return context
