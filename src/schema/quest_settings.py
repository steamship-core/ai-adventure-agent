import uuid
from typing import Optional

from pydantic import BaseModel, Field
from steamship import Steamship
from steamship.agents.schema import ChatHistory

from mixins.user_settings import UserSettings


class Quest(BaseModel):
    """Information about a quest."""

    class Config:
        arbitrary_types_allowed = True

    description: Optional[str] = Field(description="The description of the quest.")
    chat_history: Optional[ChatHistory] = Field(
        description="The chat history of the quest.", exclude=True
    )

    def create_chat_history(self, client: Steamship, user_settings: UserSettings):
        self.chat_history = ChatHistory.get_or_create(client, {"id": str(uuid.uuid4())})
        self.chat_history.append_system_message(
            f"We are writing a story about the adventure of a character named {user_settings.name}."
        )
        self.chat_history.append_system_message(
            f"{user_settings.name} has the following background: {user_settings.background}"
        )
        self.chat_history.append_system_message(
            f"{user_settings.name} has the following things in their inventory: {user_settings.inventory}"
        )
        self.chat_history.append_system_message(
            f"{user_settings.name}'s motivation is to {user_settings.motivation}"
        )
        self.chat_history.append_system_message(
            f"The tone of this story is {user_settings.tone}"
        )
        prepared_mission_summaries = "\n".join(user_settings.mission_summaries)
        if len(user_settings.mission_summaries) > 0:
            self.chat_history.append_system_message(
                f"{user_settings.name} has already been on previous missions: \n {prepared_mission_summaries}"
            )
        return self.chat_history
