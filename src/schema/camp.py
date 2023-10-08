from typing import List, Optional

from pydantic import BaseModel, Field

from schema.characters import HumanCharacter, NpcCharacter


class Camp(BaseModel):
    name: Optional[str] = Field("Camp", description="The name of the user's camp.")
    npcs: List[NpcCharacter] = Field(
        [
            NpcCharacter(
                name="Logan",
                description="A woodsman who was passing by and thought he'd join your crew.",
                category="conversational",
                background="From a small town. Grew up the youngest of three brothers. Mostly kept to himself until he a tornado swept away his whole family. Has been on his own since age 13. Knows a lot about the world. Old heart. Wise eyes. Tends to speak softly but with good advice.",
                motivation="Just passing through, but thought he'd stay for a bit.",
            )
        ],
        description="The list of NPCs who are at the camp.",
    )
    human_players: List[HumanCharacter] = Field(
        [], description="The list of human characters that are at the camp."
    )
    chat_file_id: Optional[str] = Field(
        None, description="The chat file ID for the camp."
    )
    # TODO: Generate an image of the camp?
    # TODO: Generate background audio for the camp?
