import logging

from steamship import Steamship, SteamshipError
from steamship.agents.llms.openai import ChatOpenAI
from steamship.agents.service.agent_service import AgentService
from steamship.invocable import post
from steamship.invocable.package_mixin import PackageMixin

from agents.onboarding_agent import OnboardingAgent
from schema.game_state import ActiveMode, GameState

# An instnace is a game instance.
from utils.context_utils import RunNextAgentException


class OnboardingMixin(PackageMixin):
    """Provides endpoints for Onboarding."""

    agent_service: AgentService
    client: Steamship

    def __init__(self, client: Steamship, agent_service: AgentService):
        self.client = client
        self.agent_service = agent_service

    @post("/complete_onboarding")
    def complete_onboarding(self, **kwargs) -> bool:
        """Attempts to complete onboarding."""
        try:
            game_state = GameState.parse_obj(kwargs)
            context = self.agent_service.build_default_context()

            if game_state.active_mode != ActiveMode.ONBOARDING:
                raise SteamshipError(
                    message=f"Unable to complete onboarding -- it appears to be complete! Currently in state {game_state.active_mode.value}"
                )

            # TODO: This should really be from the agent service
            function_capable_llm = ChatOpenAI(self.client)
            self.onboarding_agent = OnboardingAgent(
                client=self.client, tools=[], llm=function_capable_llm
            )

            self.onboarding_agent.run(context)
            return True
        except RunNextAgentException:
            return True
        except BaseException as e:
            logging.exception(e)
            raise e
