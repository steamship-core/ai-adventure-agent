from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field
from steamship import Task, TaskState

from schema.camp import Camp
from schema.characters import HumanCharacter
from schema.preferences import Preferences
from schema.quest import Quest


class ActiveMode(str, Enum):
    ONBOARDING = "onboarding"
    CAMP = "camp"
    QUEST = "quest"
    NPC_CONVERSATION = "npc-conversation"


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

    profile_image_task: Optional[Task] = Field(
        default=None,
        description="Task for the generation of an initial profile image for the primary character.",
    )

    chat_history_for_onboarding_complete: Optional[bool] = Field(
        default=None,
        description="Whether the onboarding profile has been written to the chat history",
    )

    def update_from_web(self, other: "GameState"):
        """Perform a gentle update so that the website doesn't accidentally blast over this if it diverges in
        structure."""
        if other.genre:
            self.genre = other.genre
        if other.tone:
            self.tone = other.tone
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
            and self.genre is not None
            and self.tone is not None
            and self.chat_history_for_onboarding_complete
        )

    def image_generation_requested(self) -> bool:
        if not self.profile_image_task:
            return False
        if task := self.profile_image_task:
            # retry if failed.
            return task.state in [
                TaskState.succeeded,
                TaskState.running,
                TaskState.waiting,
            ]

    def dict(self, **kwargs) -> dict:
        """Return the dict representation, making sure the computed properties are there."""
        ret = super().dict(**kwargs)
        ret["active_mode"] = self.active_mode.value
        return ret

    @property
    def active_mode(self) -> ActiveMode:
        if not self.is_onboarding_complete():
            return ActiveMode.ONBOARDING
        if self.in_conversation_with:
            return ActiveMode.NPC_CONVERSATION
        if self.current_quest:
            return ActiveMode.QUEST
        return ActiveMode.CAMP
