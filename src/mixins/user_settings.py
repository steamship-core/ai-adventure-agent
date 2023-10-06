from typing import List, Optional

from pydantic import BaseModel, Field
from steamship import Steamship
from steamship.invocable import get, post
from steamship.invocable.package_mixin import PackageMixin
from steamship.utils.kv_store import KeyValueStore

# An instnace is a game instance.
from schema.characters import HumanCharacter, NpcCharacter
from schema.quest_settings import Quest


class Camp(BaseModel):
    name: Optional[str]
    npcs: List[NpcCharacter]
    human_players: List[HumanCharacter]
    chat_file_id: Optional[str]

    """Todo: NPCs and Trader, images, etc."""


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

    camp: Optional[Camp] = Field()

    def save(self, context_id: str, client: Steamship) -> dict:
        """Save UserSettings to the KeyValue store."""
        key = f"UserSettings-{context_id}"
        value = self.dict()
        kv = KeyValueStore(client, key)
        kv.set(key, value)
        return value

    @staticmethod
    def load(context_id: str, client: Steamship) -> "UserSettings":
        """Save UserSettings to the KeyValue store."""
        key = f"UserSettings-{context_id}"
        kv = KeyValueStore(client, key)
        try:
            value = kv.get(key)
            return UserSettings.parse_obj(value)
        except BaseException:
            return UserSettings()


class UserSettingsMixin(PackageMixin):
    """Provides endpoints for User Settings."""

    client: Steamship

    def __init__(self, client: Steamship):
        self.client = client

    @post("/user_settings")
    def post_user_settings(self, context_id: str, **kwargs) -> dict:
        """Set the user settings."""
        user_settings = UserSettings.parse_obj(kwargs)
        return user_settings.save(context_id, self.client)

    @get("/user_settings")
    def get_user_settings(self, context_id: str) -> dict:
        """Get the user settings."""
        return UserSettings.load(context_id=context_id, client=self.client).dict()
