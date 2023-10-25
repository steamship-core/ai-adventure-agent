from typing import List, Optional

from pydantic import BaseModel, Field

from schema.characters import HumanCharacter, NpcCharacter
from schema.objects import Item


class Camp(BaseModel):
    name: Optional[str] = Field("Camp", description="The name of the user's camp.")
    npcs: List[NpcCharacter] = Field(
        [
            NpcCharacter(
                name="The Merchant",
                description="A merchant who sells items. He heard of your adventures and offers to sell you some items or buy those you don't need.",
                category="merchant",
                background="A mysterious roaming merchant. Friend of nobody and yet open to all. He passes through from time to time, always with a mysterious air and a cart full of intresting inventory.",
                motivation="Will buy and sell items for gold.",
                inventory=[
                    Item(name="A mysterious orb. It glows with a strange energy.")
                ],
            ),
        ],
        description="The list of NPCs who are at the camp.",
    )
    human_players: List[HumanCharacter] = Field(
        [], description="The list of human characters that are at the camp."
    )
    chat_file_id: Optional[str] = Field(
        None, description="The chat file ID for the camp."
    )
    image_block_url: Optional[str] = Field(
        None,
        description="Public URL of a block containing a generated (or generating) image of camp",
    )
    audio_block_url: Optional[str] = Field(
        None,
        description="Public URL of a block containing a generated (or generating) background music of camp",
    )
