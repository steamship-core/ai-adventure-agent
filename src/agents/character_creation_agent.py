from steamship import Block, MimeTypes, PluginInstance, Steamship
from steamship.agents.schema import Action, Agent, AgentContext
from steamship.agents.schema.action import FinishAction

from mixins.server_settings import ServerSettings


class CharacterCreationAgent(Agent):
    """
    DESIGN GOALS:
    This implements the "create a character flow" and only that.
    It can be slotted into as a state machine sub-agent by the overall agent.

    NOTE:
    The web site will actually take care of this so we technically don't need this.
    This is just to help the agent-side develop things in a way that doesn't require the web to work.
    It also holds a finger on the possibility that we might run in "only Slack" mode or something without a web site.
    """

    client: Steamship
    server_settings: ServerSettings

    voice_generator: PluginInstance
    image_generator: PluginInstance

    PROMPT = ""

    def record_action_run(self, action: Action, context: AgentContext):
        pass

    def next_action(self, context: AgentContext) -> Action:
        return FinishAction(
            output=[
                Block(
                    text="TODO: Character creation flow and persistence.",
                    mime_type=MimeTypes.MKD,
                )
            ]
        )
