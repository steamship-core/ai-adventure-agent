from typing import List, Optional

from pydantic import BaseModel, Field


class UserSettings(BaseModel):
    """Settings for a user of the game.

    Note from Max: The Web UI will likely have a form that collects some of this information and seed it into the game in advance.
    This means that the AI might not need to set everything.
    """

    name: Optional[str] = Field(description="The name of the character.")
    description: Optional[str] = Field(description="The description of the character.")
    background: Optional[str] = Field(description="The background of the character.")
    inventory: Optional[str] = Field(description="The inventory of the character.")
    motivation: Optional[str] = Field(description="The motivation of the character.")
    tone: Optional[str] = Field(description="The tone of the story being told.")
    mission_summaries: List[str] = Field(
        [], description="The missions that the character has been on."
    )

    # These are computed; stored throughout the game

    image_url: Optional[str] = Field(description="The image URL of the character.")
