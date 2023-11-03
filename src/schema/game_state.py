from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

from schema.camp import Camp
from schema.characters import HumanCharacter, NpcCharacter
from schema.preferences import Preferences
from schema.quest import Quest, QuestDescription


class ActiveMode(str, Enum):
    ONBOARDING = "onboarding"
    CAMP = "camp"
    QUEST = "quest"
    NPC_CONVERSATION = "npc-conversation"
    DIAGNOSTIC = "diagnostic"


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

    preferences: Preferences = Field(
        Preferences(), description="Player's game preferences"
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

    quest_arc: Optional[List[QuestDescription]] = Field(
        default=None,
        description="The list of stages of quest that a player will go through",
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

    profile_image_url: Optional[str] = Field(
        default=None, description="The URL for the character image"
    )

    chat_history_for_onboarding_complete: Optional[bool] = Field(
        default=None,
        description="Whether the onboarding profile has been written to the chat history",
    )

    diagnostic_mode: Optional[str] = Field(
        default=None, description="The name of the remote diagnostic test to run"
    )

    def update_from_web(self, other: "GameState"):
        """Perform a gentle update so that the website doesn't accidentally blast over this if it diverges in
        structure."""

        # Allow zeroing out even if it's None
        self.diagnostic_mode = other.diagnostic_mode

        if other.player:
            self.player.update_from_web(other.player)
        if other.preferences:
            self.preferences.update_from_web(other.preferences)

    def is_onboarding_complete(self) -> bool:
        """Return True if the player onboarding has been completed.

        This is used by api.pyu to decide whether to route to the ONBOARDING AGENT.
        """
        return (
            self.player is not None
            and self.player.is_onboarding_complete()
            and self.chat_history_for_onboarding_complete
        )

    def image_generation_requested(self) -> bool:
        if self.player.profile_image_url:
            return True
        elif self.profile_image_url:
            return True
        else:
            return False

    def camp_image_requested(self) -> bool:
        return True if self.camp.image_block_url else False

    def camp_audio_requested(self) -> bool:
        return True if self.camp.audio_block_url else False

    def dict(self, **kwargs) -> dict:
        """Return the dict representation, making sure the computed properties are there."""
        ret = super().dict(**kwargs)
        ret["active_mode"] = self.active_mode.value
        return ret

    @property
    def active_mode(self) -> ActiveMode:
        if self.diagnostic_mode is not None:
            return ActiveMode.DIAGNOSTIC  # Diagnostic mode takes precedence
        if not self.is_onboarding_complete():
            return ActiveMode.ONBOARDING
        if self.in_conversation_with:
            return ActiveMode.NPC_CONVERSATION
        if self.current_quest:
            return ActiveMode.QUEST
        return ActiveMode.CAMP

    def find_npc(self, npc_name: str) -> Optional[NpcCharacter]:
        if self.camp and self.camp.npcs:
            for npc in self.camp.npcs:
                if npc.name == npc_name:
                    return npc
        return None
