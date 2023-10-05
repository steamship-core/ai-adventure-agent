from typing import Optional

from steamship import PluginInstance, Steamship
from steamship.agents.schema import Action, Agent, AgentContext

from character_creation_agent import CharacterCreationAgent
from quest_agent import QuestAgent
from schema import ServerSettings, UserSettings


class GameAgent(Agent):
    """
    GOAL: Implement an agent that streams back things.
    """

    client: Steamship

    server_settings: Optional[ServerSettings]
    user_settings: Optional[UserSettings]

    llm: Optional[PluginInstance]
    image_generator: Optional[PluginInstance]
    voice_generator: Optional[PluginInstance]

    PROMPT = ""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Init Settings Objects
        self.server_settings = ServerSettings()
        self.user_settings = UserSettings()

    def record_action_run(self, action: Action, context: AgentContext):
        pass

    def next_action(self, context: AgentContext) -> Action:
        # Add the server settings & generators to the context
        context = self.server_settings.add_to_agent_context(context)

        if not self.user_settings or not self.user_settings.is_character_completed():
            print("Character")
            sub_agent = CharacterCreationAgent(
                tools=[],
                llm=self.llm,
            )
        else:
            # The character is completed! Go on a quest!
            print("Quest")
            sub_agent = QuestAgent(
                tools=[],
                llm=self.llm,
                user_settings=self.user_settings,
            )

        return sub_agent.next_action(context)


if __name__ == "__main__":
    g = GameAgent(tools=[], client=Steamship(), llm=None)
