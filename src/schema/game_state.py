from typing import List, Optional

from pydantic import BaseModel, Field

from schema.camp import Camp
from schema.characters import HumanCharacter
from schema.quest import Quest


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

    tone: Optional[str] = Field(None, description="The tone of the story being told.")
    genre: Optional[str] = Field(None, description="The genre of the story being told.")
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
            and self.player.is_onboarding_complete()
            and self.genre is not None
            and self.tone is not None
        )
