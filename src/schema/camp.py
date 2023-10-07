from typing import List, Optional

from pydantic import BaseModel, Field

from schema.characters import HumanCharacter, NpcCharacter


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
