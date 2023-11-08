from steamship import Steamship, SteamshipError
from steamship.agents.llms.openai import ChatOpenAI
from steamship.agents.service.agent_service import AgentService
from steamship.invocable import post
from steamship.invocable.package_mixin import PackageMixin

from agents.onboarding_agent import OnboardingAgent
from schema.game_state import ActiveMode

# An instnace is a game instance.
from utils.context_utils import RunNextAgentException, get_game_state
from utils.error_utils import record_and_throw_unrecoverable_error
from utils.generation_utils import generate_story_intro


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
            context = self.agent_service.build_default_context()
            game_state = get_game_state(context)

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
            return game_state.chat_history_for_onboarding_complete
        except BaseException as e:
            context = self.agent_service.build_default_context()
            record_and_throw_unrecoverable_error(e, context)

    @post("/generate_story_intro")
    def generate_story_intro(self) -> str:
        try:
            context = self.agent_service.build_default_context()
            game_state = get_game_state(context)
            story_intro = generate_story_intro(
                player=game_state.player, context=context
            )
            return story_intro
        except BaseException as e:
            context = self.agent_service.build_default_context()
            record_and_throw_unrecoverable_error(e, context)
