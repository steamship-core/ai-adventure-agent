import json
import logging
from typing import List, Optional, Type, cast

from pydantic import Field
from steamship import Steamship
from steamship.agents.llms.openai import ChatOpenAI
from steamship.agents.logging import AgentLogging
from steamship.agents.mixins.transports.slack import (
    SlackTransport,
    SlackTransportConfig,
)
from steamship.agents.mixins.transports.steamship_widget import SteamshipWidgetTransport
from steamship.agents.mixins.transports.telegram import (
    TelegramTransport,
    TelegramTransportConfig,
)
from steamship.agents.schema import Agent, AgentContext, Tool
from steamship.invocable import Config
from steamship.utils.repl import AgentREPL

from agents.camp_agent import CampAgent
from agents.npc_agent import NpcAgent
from agents.onboarding_agent import OnboardingAgent
from agents.quest_agent import QuestAgent
from endpoints.game_state_endpoints import GameStateMixin
from endpoints.image_endpoints import ImageMixin
from endpoints.music_endpoints import MusicMixin
from endpoints.npc_endpoints import NpcMixin
from endpoints.quest_endpoints import QuestMixin
from endpoints.server_endpoints import ServerSettingsMixin
from utils.agent_service import AgentService
from utils.context_utils import get_game_state


class AdventureGameService(AgentService):
    """Deployable game that runs an instance of a magical AI Adventure Game.

    Each player's game is an INSTANCE of this service, with its own API & Chat Endpoints.

    The game is implemented as a series of AGENTS --- only one of which has control at any given time:

    - CAMP AGENT        interacts with you when you're at camp -- not on a quest
    - QUEST AGENT       guides you through a magical quest
    - NPC AGENT         converses with you as any NPC you encounter in the game
    - ONBOARDING AGENT  walks you through initial onboarding

    GAMEPLAY
    ========

    The basic flow of the game is as follows:
      - If necessary, Onboarding Agent takes information from you (the web UI may provide this)
      - The player arrives at camp
      - Player uses energy to go out on a fun quest
        - Player finds new items!
        - Player gains a new rank!
        - Player returns to camp

    While at camp, the player (maybe) can chat with his camp-mates.

    RUNNING
    =======

    The entire game can be played from the cammand line (ship run local) in text mode, however
    it is designed to be played with a graphical front-end you can deploy to Vercel. This adds a lot of awesome
    above and beyond text-mode: music, images, voice... But look: if you want to be an 80s kid and command-line it,
    we salute you.

    THIS CLASS
    ==========

    Read this class as a top-level registry:

    - Mixins, which add:
      - The capability to connect a game to Slack, Telegram, etc
      - API endpoints for coordination with the web app

    - Agent registrations:
      - Onboarding Agent
      - Camp Agent
      - Quest Agent
      - NPC Agent

    - Context registration
      - Loading the associated AI models into the AgentContext
      - Loading the associated game state
    """

    context: Optional[AgentContext] = None

    USED_MIXIN_CLASSES = [
        SteamshipWidgetTransport,  # Adds compatibility with Steamship's Hosting Panel
        TelegramTransport,  # Adds compatibility with Telegram
        SlackTransport,  # Adds compatibility with Slack
        GameStateMixin,  # Provides API Endpoints for User Management (used by the associated web app)
        ServerSettingsMixin,  # Provides API Endpoints for Server Management (used by the associated web app)
        QuestMixin,  # Provides API Endpoints for Quest Management (used by the associated web app)
        NpcMixin,  # Provides API Endpoints for NPC Chat Management (used by the associated web app)
        ImageMixin,  # Provides API Endpoints for Image Generation
        MusicMixin,  # Provides API Endpoints for Music Generation
    ]
    """USED_MIXIN_CLASSES tells Steamship what additional HTTP endpoints to register on your AgentService."""

    class BasicAgentServiceConfig(Config):
        """Pydantic definition of the user-settable Configuration of this Agent."""

        telegram_bot_token: str = Field(
            "", description="[Optional] Secret token for connecting to Telegram"
        )
        eleven_labs_voice_id: str = Field(
            "pNInz6obpgDQGcFmaJgB",
            description="[Optional] ElevenLabs voice ID (default: Adam)",
        )

    config: BasicAgentServiceConfig
    """The configuration block that users who create an instance of this agent will provide."""

    tools: List[Tool]
    """The list of Tools that this agent is capable of using."""

    @classmethod
    def config_cls(cls) -> Type[Config]:
        """Return the Configuration class so that Steamship can auto-generate a web UI upon agent creation time."""
        return AdventureGameService.BasicAgentServiceConfig

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Communication Transport Setup
        # -----------------------------

        # Support Steamship's web client
        self.add_mixin(
            SteamshipWidgetTransport(
                client=self.client,
                agent_service=cast(AgentService, self),
            )
        )

        # Support Slack
        self.add_mixin(
            SlackTransport(
                client=self.client,
                config=SlackTransportConfig(),
                agent_service=cast(AgentService, self),
            )
        )

        # Support Telegram
        self.add_mixin(
            TelegramTransport(
                client=self.client,
                config=TelegramTransportConfig(
                    bot_token=self.config.telegram_bot_token
                ),
                agent_service=cast(AgentService, self),
            )
        )

        # APIs for Controlling the Game
        # -----------------------------

        # API for getting and setting server settings
        self.add_mixin(ServerSettingsMixin(client=self.client))

        # API for getting and setting game state
        self.add_mixin(
            GameStateMixin(client=self.client, agent_service=cast(AgentService, self))
        )

        # API for getting and setting game state
        self.add_mixin(
            QuestMixin(client=self.client, agent_service=cast(AgentService, self))
        )

        # API for getting and setting game state
        self.add_mixin(
            NpcMixin(client=self.client, agent_service=cast(AgentService, self))
        )

        self.add_mixin(
            ImageMixin(client=self.client, agent_service=cast(AgentService, self))
        )

        self.add_mixin(
            MusicMixin(client=self.client, agent_service=cast(AgentService, self))
        )

        # Instantiate the core game agents
        function_capable_llm = ChatOpenAI(self.client)

        self.onboarding_agent = OnboardingAgent(
            client=self.client, tools=[], llm=function_capable_llm
        )
        self.quest_agent = QuestAgent(tools=[], llm=function_capable_llm)
        self.camp_agent = CampAgent(llm=function_capable_llm)
        self.npc_agent = NpcAgent(llm=function_capable_llm)

    def get_default_agent(self, throw_if_missing: bool = True) -> Optional[Agent]:
        """Returns the active agent.

        The game is built with different agents which manage different aspects of the game.

        This method is uses the global GAME STATE to select which agent is active.

        - If game_state.is_onboarding_complete: ONBOARDING AGENT
        - If game_state.in_conversation_with: NPC AGENT
        - If game_state.current_quest: QUEST AGENT
        - Else: CAMP AGENT
        """
        context = self.build_default_context()
        game_state = get_game_state(context)

        logging.info(
            f"Game State: {json.dumps(game_state.dict())}.",
            extra={
                AgentLogging.IS_MESSAGE: True,
                AgentLogging.MESSAGE_TYPE: AgentLogging.THOUGHT,
                AgentLogging.MESSAGE_AUTHOR: AgentLogging.AGENT,
            },
        )

        if not game_state.is_onboarding_complete():
            # Use the ONBOARDING AGENT if we still need to collect player/game information
            sub_agent = self.onboarding_agent
        else:
            if game_state.in_conversation_with:
                # Use the NPC AGENT if we're currently in a conversation.
                sub_agent = self.npc_agent
                # DANGER: The below might mess with streaming.
                # switch_history_to_current_conversant(context)

            elif game_state.current_quest:
                # Use the QUEST AGENT if we're currently on a quest.
                sub_agent = self.quest_agent
                # DANGER: The below might mess with streaming.
                # switch_history_to_current_quest(context)
            else:
                # Use the CAMP AGENT as the default. This is like the home base router.
                sub_agent = self.camp_agent

        logging.info(
            f"Selecting Agent: {sub_agent.__class__.__name__}.",
            extra={
                AgentLogging.IS_MESSAGE: True,
                AgentLogging.MESSAGE_TYPE: AgentLogging.THOUGHT,
                AgentLogging.MESSAGE_AUTHOR: AgentLogging.AGENT,
            },
        )

        return sub_agent


if __name__ == "__main__":
    # AgentREPL provides a mechanism for local execution of an AgentService method.
    # This is used for simplified debugging as agents and tools are developed and
    # added.

    # NOTE: There's a bug in the repl where it doesn't respect my workspace selection below. It always creates a new one.
    client = Steamship(workspace="snugly-crater-i8mli")
    repl = AgentREPL(
        cast(AgentService, AdventureGameService), agent_package_config={}, client=client
    )
    repl.run(dump_history_on_exit=True)
