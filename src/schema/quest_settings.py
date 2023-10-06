import uuid
from typing import List, Optional

from pydantic import BaseModel, Field
from steamship import Steamship
from steamship.agents.schema import ChatHistory

from schema.characters import Character, Item


class Quest(BaseModel):
    """Information about a quest."""

    # Input Fields

    name: Optional[str]

    # Metadata Fields

    chat_file_id: Optional[str]

    # Output Fields
    # These are generated after the

    image_url: Optional[List[int]]
    """An image of this quest. Ideally movie poster style."""

    text_summary: Optional[str]
    """The summary of this quest. To be written in book jacket style."""

    new_items: Optional[List[Item]]
    """New items you found on this quest."""

    rank_delta: Optional[List[int]]
    """The change in rank that resulted from this quest."""

    class Config:
        arbitrary_types_allowed = True

    description: Optional[str] = Field(description="The description of the quest.")
    chat_history: Optional[ChatHistory] = Field(
        description="The chat history of the quest.", exclude=True
    )

    def create_chat_history(self, client: Steamship, player: Character):
        self.chat_history = ChatHistory.get_or_create(client, {"id": str(uuid.uuid4())})
        self.chat_history.append_system_message(
            f"We are writing a story about the adventure of a character named {player.name}."
        )
        self.chat_history.append_system_message(
            f"{player.name} has the following background: {player.background}"
        )
        self.chat_history.append_system_message(
            f"{player.name} has the following things in their inventory: {player.inventory}"
        )
        self.chat_history.append_system_message(
            f"{player.name}'s motivation is to {player.motivation}"
        )
        # self.chat_history.append_system_message(
        #     f"The tone of this story is {user_settings.tone}"
        # )
        # prepared_mission_summaries = "\n".join([quest.text_summary for quest in user_settings.quests])
        # if len(user_settings.quests) > 0:
        #     self.chat_history.append_system_message(
        #         f"{player.name} has already been on previous missions: \n {prepared_mission_summaries}"
        #     )
        return self.chat_history
