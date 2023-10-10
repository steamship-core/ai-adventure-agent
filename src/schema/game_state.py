from typing import List, Optional

from pydantic import BaseModel, Field
from steamship import Steamship
from steamship.agents.schema import AgentContext
from steamship.utils.kv_store import KeyValueStore

from schema.camp import Camp
from schema.characters import HumanCharacter
from schema.quest import Quest

# An instnace is a game instance.
from utils.context_utils import with_game_state


class GameState(BaseModel):
    """Settings for a user of the game.

    Max Notes:

    - "Theme": E.g. Fantasy, Midevil
    - User Character - how to fetch.
    - Background images - how to fetch.
    - Campsite Images

    TODO: Identity

    """

    # BEGIN ONBOARDING FIELDS
    player: HumanCharacter = Field(
        HumanCharacter(), description="The player of the game."
    )

    tone: Optional[str] = Field(
        "Silly", description="The tone of the story being told."
    )
    genre: Optional[str] = Field(
        "Thriller", description="The genre of the story being told."
    )
    # END ONBOARDING FIELDS

    # NOTE: The fields below are not intended to be settable BY the user themselves.
    quests: List[Quest] = Field(
        [], description="The missions that the character has been on."
    )

    camp: Optional[Camp] = Field(
        Camp(),
        description="The player's camp. This is where they are then not on a quest.",
    )

    current_quest: Optional[str] = Field(
        None,
        description="The current quest-id that the character is on. This is used for game logic.",
    )

    in_conversation_with: Optional[str] = Field(
        None,
        description="The name of the NPC that the user is currently in conversation with.",
    )

    await_ask_key: Optional[str] = Field(
        None,
        description="The key of the last question asked to the user via context_utils.await_ask.",
    )

    def is_onboarding_complete(self) -> bool:
        """Return True if the player onboarding has been completed.

        This is used by api.pyu to decide whether to route to the ONBOARDING AGENT.
        """
        return (
            self.player is not None
            and self.player.name is not None
            and self.player.description is not None
            and self.player.background is not None
            and self.player.motivation is not None
            and self.player.inventory is not None
            and len(self.player.inventory) > 0
            and self.genre is not None
            and self.tone is not None
        )

    @staticmethod
    def load(client: Steamship) -> "GameState":
        """Save GameState to the KeyValue store."""
        key = "GameState"
        kv = KeyValueStore(client, key)
        try:
            value = kv.get(key)
            return GameState.parse_obj(value)
        except BaseException:
            return GameState()

    def add_to_agent_context(self, context: AgentContext) -> AgentContext:
        context = with_game_state(self, context)
        return context
