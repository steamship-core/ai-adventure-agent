import json
import logging
import pathlib
import time
from typing import Any, Dict, List, Optional, Type, Union, cast

from pydantic import Field
from pydantic_yaml import parse_yaml_raw_as
from steamship import Steamship, SteamshipError
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
from steamship.data import TagKind
from steamship.data.block import Block, StreamState
from steamship.data.tags.tag_constants import RoleTag
from steamship.invocable import Config
from steamship.utils.repl import AgentREPL

from agents.camp_agent import CampAgent
from agents.diagnostic_agent import DiagnosticAgent
from agents.generating_agent import GeneratingAgent
from agents.npc_agent import NpcAgent
from agents.onboarding_agent import OnboardingAgent
from agents.quest_agent import QuestAgent
from endpoints.camp_endpoints import CampMixin
from endpoints.game_state_endpoints import GameStateMixin
from endpoints.help_endpoints import HelpMixin
from endpoints.npc_endpoints import NpcMixin
from endpoints.onboarding_endpoints import OnboardingMixin
from endpoints.quest_endpoints import QuestMixin
from endpoints.server_endpoints import ServerSettingsMixin
from schema.characters import HumanCharacter
from schema.game_state import ActiveMode
from schema.server_settings import ServerSettings
from utils.agent_service import AgentService
from utils.context_utils import get_game_state, save_game_state, save_server_settings
from utils.tags import TagKindExtensions


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

    The entire game can be played from the command line (ship run local) in text mode, however
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
        CampMixin,  # Provides API Endpoints for Camp Management (used by the associated web app)
        NpcMixin,  # Provides API Endpoints for NPC Chat Management (used by the associated web app)
        OnboardingMixin,  # Provide API Endpoints for Onboarding
        HelpMixin,  # Provide API Endpoints for hinting, etc.,
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
        openai_api_key: str = Field(
            "",
            description="An openAI API key to use. If left default, will use Steamship's API key.",
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
        self.add_mixin(
            ServerSettingsMixin(
                client=self.client, agent_service=cast(AgentService, self)
            )
        )

        self.add_mixin(
            GameStateMixin(client=self.client, agent_service=cast(AgentService, self))
        )

        self.add_mixin(
            CampMixin(client=self.client, agent_service=cast(AgentService, self))
        )

        self.add_mixin(
            QuestMixin(client=self.client, agent_service=cast(AgentService, self))
        )

        self.add_mixin(
            NpcMixin(client=self.client, agent_service=cast(AgentService, self))
        )

        self.add_mixin(
            OnboardingMixin(
                client=self.client,
                agent_service=cast(AgentService, self),
                openai_api_key=self.config.openai_api_key,
            )
        )

        self.add_mixin(
            HelpMixin(client=self.client, agent_service=cast(AgentService, self))
        )

        # Instantiate the core game agents
        function_capable_llm = ChatOpenAI(self.client)

        self.onboarding_agent = OnboardingAgent(
            client=self.client,
            tools=[],
            llm=function_capable_llm,
            openai_api_key=self.config.openai_api_key,
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
        active_mode = game_state.active_mode

        logging.debug(
            f"Game State: {json.dumps(game_state.dict())}.",
            extra={
                AgentLogging.IS_MESSAGE: True,
                AgentLogging.MESSAGE_TYPE: AgentLogging.THOUGHT,
                AgentLogging.MESSAGE_AUTHOR: AgentLogging.AGENT,
            },
        )

        if active_mode == ActiveMode.DIAGNOSTIC:
            sub_agent = DiagnosticAgent(game_state.diagnostic_mode)
        elif active_mode == ActiveMode.ONBOARDING:
            sub_agent = self.onboarding_agent
        elif active_mode == ActiveMode.NPC_CONVERSATION:
            sub_agent = self.npc_agent
        elif active_mode == ActiveMode.QUEST:
            sub_agent = self.quest_agent
        elif active_mode == ActiveMode.CAMP:
            sub_agent = self.camp_agent
        elif active_mode == ActiveMode.GENERATING:
            # This is just a stub agent so that we don't throw an exception.
            sub_agent = GeneratingAgent()
        else:
            raise SteamshipError(message=f"Unknown mode: {active_mode}")

        logging.info(
            f"Selecting Agent: {sub_agent.__class__.__name__}.",
            extra={
                AgentLogging.IS_MESSAGE: True,
                AgentLogging.MESSAGE_TYPE: AgentLogging.THOUGHT,
                AgentLogging.MESSAGE_AUTHOR: AgentLogging.AGENT,
            },
        )

        return sub_agent


class GameREPL(AgentREPL):
    last_seen_block = 0

    def __init__(
        self,
        agent_class: Type[AgentService],
        method: Optional[str] = None,
        agent_package_config: Optional[Dict[str, Any]] = None,
        client: Optional[Steamship] = None,
        context_id: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(
            agent_class=agent_class,
            method=method,
            agent_package_config=agent_package_config,
            client=client,
            context_id=context_id,
            **kwargs,
        )
        self.agent_instance = self.agent_class(client=client, config=self.config)

    def run_with_client(self, client: Steamship, **kwargs):
        # Override so we can not clobber self.agent_instance
        try:
            from termcolor import colored  # noqa: F401
        except ImportError:

            def colored(text: str, color: str, **kwargs):
                return text

        print("Starting REPL for Agent...")
        print(
            "If you make code changes, restart this REPL. Press CTRL+C to exit at any time.\n"
        )

        # Determine the responder, which may have been custom-supplied on the agent.
        responder = getattr(self.agent_instance, self.method or "prompt")
        while True:
            input_text = input(colored(text="Input: ", color="blue"))  # noqa: F821
            output = responder(prompt=input_text, context_id=self.context_id, **kwargs)
            self.print_object_or_objects(output)

    def print_object_or_objects(
        self, output: Union[List, Any], metadata: Optional[Dict[str, Any]] = None
    ):
        context = AgentContext.get_or_create(
            client=self.agent_instance.client,
            context_keys={"id": "default"},
            searchable=False,
        )
        for block in context.chat_history.file.blocks:
            if block.index_in_file > self.last_seen_block:
                if block.stream_state == StreamState.STARTED:
                    start_time = time.perf_counter()
                    while (
                        block.stream_state
                        not in [
                            StreamState.COMPLETE,
                            StreamState.ABORTED,
                        ]
                        and (time.perf_counter() - start_time) < 30
                    ):
                        time.sleep(0.4)
                        block = Block.get(block.client, _id=block.id)
            self.print_new_block(block)
        self.last_seen_block = context.chat_history.file.blocks[-1].index_in_file
        super().print_object_or_objects(output, metadata)

    def print_new_block(self, block: Block):
        tag_kinds = {tag.kind for tag in block.tags}
        # tag_names = {tag.name for tag in block.tags}
        if (
            TagKind.STATUS_MESSAGE not in tag_kinds
            and TagKindExtensions.INSTRUCTIONS not in tag_kinds
            and block.chat_role not in [RoleTag.USER]
        ):
            tag_texts = "".join(
                sorted({f"[{tag.kind},{tag.name}]" for tag in block.tags})
            )
            if block.is_text():
                print(f"{tag_texts} {block.text}\n")
            else:
                print(f"{tag_texts} {block.raw_data_url}")


if __name__ == "__main__":
    basepath = pathlib.Path(__file__).parent.resolve()
    with open(basepath / "../example_content/evil_science.yaml") as settings_file:
        yaml_string = settings_file.read()
        server_settings = parse_yaml_raw_as(ServerSettings, yaml_string)

    with open(basepath / "../example_content/christine.yaml") as character_file:
        yaml_string = character_file.read()
        character = parse_yaml_raw_as(HumanCharacter, yaml_string)

    with Steamship.temporary_workspace() as client:
        repl = GameREPL(
            cast(AgentService, AdventureGameService),
            agent_package_config={},
            client=client,
        )
        context = repl.agent_instance.build_default_context()
        save_server_settings(server_settings, context)
        game_state = get_game_state(context)
        game_state.player = character
        save_game_state(game_state, context)

        repl.run()  # dumping history seems to provide empty results, so removing
