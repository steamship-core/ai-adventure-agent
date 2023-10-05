from typing import List, Type

from pydantic import Field
from steamship.agents.llms.openai import ChatOpenAI
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
from steamship.agents.service.agent_service import AgentService
from steamship.invocable import Config

from game_agent import GameAgent

SYSTEM_PROMPT = """."""


class BasicAgentServiceWithPersonalityAndVoice(AgentService):
    """Deployable Multimodal Bot that lets you generate Stable Diffusion images.

    Comes with out of the box support for:
    - Telegram
    - Slack
    - Web Embeds

    """

    USED_MIXIN_CLASSES = [SteamshipWidgetTransport, TelegramTransport, SlackTransport]
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
        return BasicAgentServiceWithPersonalityAndVoice.BasicAgentServiceConfig

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Tools Setup
        # -----------

        # Tools can return text, audio, video, and images. They can store & retrieve information from vector DBs, and
        # they can be stateful -- using Key-Valued storage and conversation history.
        #
        # See https://docs.steamship.com for a full list of supported Tools.
        self.tools = []

        # Agent Setup
        # ---------------------

        # This agent's planner is responsible for making decisions about what to do for a given input.
        agent = GameAgent(
            tools=[],
            llm=ChatOpenAI(self.client, model_name="gpt-4"),
            client=self.client,
        )

        # Here is where we override the agent's prompt to set its personality. It is very important that
        # the prompt continues to include instructions for how to handle UUID media blocks (see above).
        agent.PROMPT = SYSTEM_PROMPT
        self.set_default_agent(agent)

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

    def run_agent(self, agent: Agent, context: AgentContext):
        """Override run-agent to patch in audio generation as a finishing step for text output."""
        # speech = GenerateSpeechTool()
        # speech.generator_plugin_config = {"voice_id": self.config.eleven_labs_voice_id}

        # def to_speech_if_text(block: Block):
        #     nonlocal speech
        #     if not block.is_text():
        #         return block

        #     output_blocks = speech.run([block], context)
        #     return output_blocks[0]

        # # Note: EmitFunc is Callable[[List[Block], Metadata], None]
        # def wrap_emit(emit_func: EmitFunc):
        #     def wrapper(blocks: List[Block], metadata: Metadata):
        #         blocks = [to_speech_if_text(block) for block in blocks]
        #         return emit_func(blocks, metadata)

        #     return wrapper

        # context.emit_funcs = [wrap_emit(emit_func) for emit_func in context.emit_funcs]
        super().run_agent(agent, context)
