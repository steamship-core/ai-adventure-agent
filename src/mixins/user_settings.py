from typing import List, Optional

from pydantic import BaseModel, Field
from steamship import Steamship
from steamship.agents.schema import AgentContext
from steamship.invocable import get, post
from steamship.invocable.package_mixin import PackageMixin
from steamship.utils.kv_store import KeyValueStore

# An instnace is a game instance.
from context_utils import with_user_settings
from schema.characters import HumanCharacter, NpcCharacter
from schema.quest_settings import Quest


class Camp(BaseModel):
    name: Optional[str] = Field("Camp", description="The name of the user's camp.")
    npcs: List[NpcCharacter] = Field(
        [], description="The list of NPCs who are at the camp."
    )
    human_players: List[HumanCharacter] = Field(
        [], description="The list of human characters that are at the camp."
    )
    chat_file_id: Optional[str] = Field(
        None, description="The chat file ID for the camp."
    )
    # TODO: Generate an image of the camp?
    # TODO: Generate background audio for the camp?


class UserSettings(BaseModel):
    """Settings for a user of the game.

    Max Notes:

    - "Theme": E.g. Fantasy, Midevil
    - User Character - how to fetch.
    - Background images - how to fetch.
    - Campsite Images

    TODO: Identity

    """

    player: HumanCharacter = Field(
        HumanCharacter(), description="The player of the game."
    )

    tone: Optional[str] = Field(
        "Silly", description="The tone of the story being told."
    )
    theme: Optional[str] = Field(
        "Fantasy", description="The genre of the story being told."
    )

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

    def save(self, client: Steamship) -> dict:
        """Save UserSettings to the KeyValue store."""
        key = "UserSettings"
        value = self.dict()
        kv = KeyValueStore(client, key)
        kv.set(key, value)
        return value

    @staticmethod
    def load(client: Steamship) -> "UserSettings":
        """Save UserSettings to the KeyValue store."""
        key = "UserSettings"
        kv = KeyValueStore(client, key)
        try:
            value = kv.get(key)
            return UserSettings.parse_obj(value)
        except BaseException:
            return UserSettings()

    def add_to_agent_context(self, context: AgentContext) -> AgentContext:
        context = with_user_settings(self, context)
        return context


class UserSettingsMixin(PackageMixin):
    """Provides endpoints for User Settings."""

    client: Steamship

    def __init__(self, client: Steamship):
        self.client = client

    @post("/user_settings")
    def post_user_settings(self, **kwargs) -> dict:
        """Set the user settings."""
        user_settings = UserSettings.parse_obj(kwargs)
        return user_settings.save(self.client)

    @get("/user_settings")
    def get_user_settings(self) -> dict:
        """Get the user settings."""
        return UserSettings.load(client=self.client).dict()
