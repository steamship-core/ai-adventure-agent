import logging
from typing import List, Optional, Type

from pydantic import Field
from steamship import Block
from steamship.agents.llms.openai import ChatOpenAI
from steamship.agents.logging import AgentLogging, StreamingOpts
from steamship.agents.mixins.transports.slack import (
    SlackTransport,
    SlackTransportConfig,
)
from steamship.agents.mixins.transports.steamship_widget import SteamshipWidgetTransport
from steamship.agents.mixins.transports.telegram import (
    TelegramTransport,
    TelegramTransportConfig,
)
from steamship.agents.schema import Action, Agent, AgentContext, Tool
from steamship.agents.service.agent_service import AgentService
from steamship.agents.utils import with_llm
from steamship.invocable import Config
from steamship.utils.repl import AgentREPL

from agents.camp_agent import CampAgent
from agents.npc_agent import NpcAgent
from agents.onboarding_agent import OnboardingAgent
from agents.quest_agent import QuestAgent
from endpoints.game_state_endpoints import GameStateMixin
from endpoints.npc_endpoints import NpcMixin
from endpoints.quest_endpoints import QuestMixin
from endpoints.server_endpoints import ServerSettingsMixin
from schema.game_state import GameState
from schema.server_settings import ServerSettings
from utils.context_utils import (
    ActivateNextAgentException,
    append_to_chat_history_and_emit,
    get_game_state,
    switch_history_to_current_conversant,
    switch_history_to_current_quest,
)


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
                agent_service=self,
            )
        )

        # Support Slack
        self.add_mixin(
            SlackTransport(
                client=self.client,
                config=SlackTransportConfig(),
                agent_service=self,
            )
        )

        # Support Telegram
        self.add_mixin(
            TelegramTransport(
                client=self.client,
                config=TelegramTransportConfig(
                    bot_token=self.config.telegram_bot_token
                ),
                agent_service=self,
            )
        )

        # APIs for Controlling the Game
        # -----------------------------

        # API for getting and setting server settings
        self.add_mixin(ServerSettingsMixin(client=self.client))

        # API for getting and setting game state
        self.add_mixin(GameStateMixin(client=self.client, agent_service=self))

        # API for getting and setting game state
        self.add_mixin(QuestMixin(client=self.client, agent_service=self))

        # API for getting and setting game state
        self.add_mixin(NpcMixin(client=self.client, agent_service=self))

        # Instantiate the core game agents
        function_capable_llm = ChatOpenAI(self.client)

        self.onboarding_agent = OnboardingAgent(
            client=self.client, tools=[], llm=function_capable_llm
        )
        self.quest_agent = QuestAgent(tools=[], llm=function_capable_llm)
        self.camp_agent = CampAgent(llm=function_capable_llm)
        self.npc_agent = NpcAgent(llm=function_capable_llm)

    def build_default_context(
        self, context_id: Optional[str] = None, **kwargs
    ) -> AgentContext:
        """Load the context for the agent.

        The AgentContext is a single place to implement (or override) the all context and state that will be used by
        the different components of the game.

        You can fetch many things from it using fetchers in `context_utils.py` such as:

        - get_game_state
        - get_server_settings
        - get_background_image_generator
        - etc

        This provides any piece of code, anywhere in the codebase, access to the correct objects
        for generating different kinds of assets and fetching/saving different kinds of state.

        INTERNAL NOTE:
        We override AgentService's context so that we can remove the get_default_agent() call from it. In AgentService,
        this method depends upon get_default_agent. In this class, that dependency is flipped.
        """
        if self.context is not None:
            return self.context  # Used cached copy

        # AgentContexts serve to allow the AgentService to run agents
        # with appropriate information about the desired tasking.
        if context_id is not None:
            logging.warning(
                "This agent ALWAYS uses the context id `default` since it is a game occuping an entire workspace, not confined to a single chat history. "
                f"The provided context_id of {context_id} will be ignored. This is to prevent surprising state errors."
            )

        # NOTA BENE!
        context_id = "default"

        use_llm_cache = self.use_llm_cache
        if runtime_use_llm_cache := kwargs.get("use_llm_cache"):
            use_llm_cache = runtime_use_llm_cache

        use_action_cache = self.use_action_cache
        if runtime_use_action_cache := kwargs.get("use_action_cache"):
            use_action_cache = runtime_use_action_cache

        include_agent_messages = kwargs.get("include_agent_messages", True)
        include_llm_messages = kwargs.get("include_llm_messages", True)
        include_tool_messages = kwargs.get("include_tool_messages", True)

        context = AgentContext.get_or_create(
            client=self.client,
            request_id=self.client.config.request_id,
            context_keys={"id": f"{context_id}"},
            use_llm_cache=use_llm_cache,
            use_action_cache=use_action_cache,
            streaming_opts=StreamingOpts(
                include_agent_messages=include_agent_messages,
                include_llm_messages=include_llm_messages,
                include_tool_messages=include_tool_messages,
            ),
            initial_system_message="",  # None necessary
        )

        # Add a default LLM to the context, using the Agent's if it exists.
        llm = ChatOpenAI(client=self.client)
        context = with_llm(context=context, llm=llm)

        # Now add in the Server Settings
        server_settings = ServerSettings()
        context = server_settings.add_to_agent_context(context)

        # Now add in the Game State
        game_state = GameState.load(self.client)
        context = game_state.add_to_agent_context(context)

        return context

    def get_default_agent(self, throw_if_missing: bool = True) -> Optional[Agent]:
        """Returns the active agent at any one time.

        This method is used by the AgentService base class to fetch which agent is supposed to be active.

        WARNING: Are there any dangers if an agent with a set of tools enqueues actions... but then the active
        agent switches and can't take them? We'll find out during gameplay..
        """
        context = self.build_default_context()
        game_state = get_game_state(context)

        # TODO: We need some way to have a hook for agent transitions. I think this belongs in the Tools given the
        # way they're used to transition. That way agents can greet you and then say goodbye so you know what's happening.

        if not game_state.is_onboarding_complete():
            # Use the ONBOARDING AGENT if we still need to collect player/game information
            sub_agent = self.onboarding_agent
        else:
            if game_state.in_conversation_with:
                # Use the NPC AGENT if we're currently in a conversation.
                sub_agent = self.npc_agent
                switch_history_to_current_conversant(context)

            elif game_state.current_quest:
                # Use the QUEST AGENT if we're currently on a quest.
                sub_agent = self.quest_agent
                switch_history_to_current_quest(context)
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

    def next_action(
        self, agent: Agent, input_blocks: List[Block], context: AgentContext
    ) -> Action:
        try:
            return super().next_action(agent, input_blocks, context)
        except ActivateNextAgentException as e:
            append_to_chat_history_and_emit(context, block=e.action.output)

            # Whatever threw this exception has hopefully modified game state such that a different action
            # will now be selected.

            # TODO: Can we turn this into a for-loop so that we can apply some kind of cutoff to prevent
            # an accidental infinite loop?

            # TODO: Is there any book-keeping at the AgentService level that we need to reset here? Like
            # completed_steps? We may need to cut-in with this try/except at a higher level like run_agent
            # so that book keeping is done for us.
            next_agent = self.get_default_agent()
            return self.next_action(next_agent, input_blocks, context)


if __name__ == "__main__":
    # AgentREPL provides a mechanism for local execution of an AgentService method.
    # This is used for simplified debugging as agents and tools are developed and
    # added.
    AgentREPL(AdventureGameService, agent_package_config={}).run(
        dump_history_on_exit=True
    )
