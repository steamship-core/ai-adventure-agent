import logging
from typing import Optional

from steamship import Steamship
from steamship.agents.logging import AgentLogging
from steamship.agents.schema import Action, Agent, AgentContext

from agents.camp_agent import CampAgent
from agents.character_creation_agent import CharacterCreationAgent
from agents.quest_agent import QuestAgent
from mixins.server_settings import ServerSettings
from mixins.user_settings import UserSettings
from schema.quest_settings import Quest


class GameAgent(Agent):
    """Agent responsible for the overall Game.

    It operates like a state machine:

    - Deferring to the CHARACTER CREATION AGENT if a character is not yet created.
    - Defaulting to the CAMP AGENT if not on a quest.
    - Deferring to the QUEST AGENT if out on a quest.

    The basic flow of the game is as follows:

    - Player arrives at camp.
    - Player uses energy to go out on a fun quest
    - Player finds new items and gains a new rank
    - Player returns to camp

    While at camp, the player can chat with his camp-mates.
    """

    client: Steamship
    server_settings: Optional[ServerSettings]
    user_settings: Optional[UserSettings]

    PROMPT = ""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Init Settings Objects
        self.server_settings = ServerSettings()
        self.user_settings = UserSettings.load(self.client)

    def next_action(self, context: AgentContext) -> Action:
        """Select the next action to perform, which might involve deferring to another Agent."""
        # Add the server settings & generators to the context
        context = self.server_settings.add_to_agent_context(context)

        # HACK until sync w/ Max - always be on a quest
        self.user_settings.current_quest = "Foo"

        if (
            not self.user_settings
            or not self.user_settings.player.is_character_completed()
        ):
            sub_agent = CharacterCreationAgent(tools=[], llm=None)
        else:
            if self.user_settings.current_quest is None:
                sub_agent = CampAgent(
                    tools=[], llm=None, user_settings=self.user_settings
                )
            else:
                quest = None
                for quest in self.user_settings.quests:
                    if quest.name == self.user_settings.current_quest:
                        quest = quest
                if quest is None:
                    quest = Quest()
                sub_agent = QuestAgent(
                    tools=[], llm=None, user_settings=self.user_settings, quest=quest
                )

        logging.info(
            f"Deferring to sub-agent: {sub_agent.__class__.__name__}.",
            extra={
                AgentLogging.IS_MESSAGE: True,
                AgentLogging.MESSAGE_TYPE: AgentLogging.THOUGHT,
                AgentLogging.MESSAGE_AUTHOR: AgentLogging.AGENT,
            },
        )

        # Defer to the right agent.
        return sub_agent.next_action(context)


if __name__ == "__main__":
    g = GameAgent(tools=[], client=Steamship(), llm=None)
