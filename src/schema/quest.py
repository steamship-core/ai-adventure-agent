from typing import List, Optional

from pydantic import BaseModel, Field

from schema.characters import Item


class Quest(BaseModel):
    """Information about a quest."""

    class Config:
        arbitrary_types_allowed = True

    # Input Fields
    originating_string: Optional[str] = Field(
        None, description="The originating string that was used to generate the Quest."
    )
    name: Optional[str] = Field(
        None,
        description="The name of the quest. AI Generated from the originating_string.",
    )
    description: Optional[str] = Field(
        None, description="The description of the quest."
    )

    # Metadata Fields
    chat_file_id: Optional[str] = Field(
        None, description="The ChatFile ID of the quest."
    )

    # Output Fields
    image_url: Optional[List[int]] = Field(
        None, description="An image of this quest generated afterwards by AI."
    )
    text_summary: Optional[str] = Field(
        None, description="A summary of the quest generated afterwards."
    )
    new_items: Optional[List[Item]] = Field(
        None, description="Any new items the player got while on the quest."
    )
    rank_delta: Optional[List[int]] = Field(
        1, description="The change in rank that resulted from this quest."
    )
