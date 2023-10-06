from typing import Optional

from pydantic import BaseModel


class Item(BaseModel):
    name: Optional[str]
    description: Optional[str]
    is_one_time_use: Optional[bool]

    modifier: Optional[int]
    """Modifier is a placeholder for the future. The game settings can assigne int->String values like "mythic", etc."""

    picture_url: Optional[str]
