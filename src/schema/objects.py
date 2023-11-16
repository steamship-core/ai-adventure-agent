from typing import Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class Item(BaseModel):
    name: Optional[str]
    description: Optional[str]
    id: str = Field(default_factory=lambda: str(uuid4()))

    is_one_time_use: Optional[bool]
    """Placeholder for the future"""

    modifier: Optional[int]
    """Modifier is a placeholder for the future. The game settings can assigne int->String values like "mythic", etc."""

    picture_url: Optional[str]

    def price(self) -> int:
        return 42

    @classmethod
    def editor_demo_object(cls, item_dict: Optional[Dict] = None) -> "Item":
        if item_dict is None:
            item_dict = {}
        return cls(
            name=item_dict.get("name", "Thor's Hammer"),
            description=item_dict.get(
                "description",
                "A magical hammer used by Thor. Exudes power and a glistening rainbow shean. Enables the bearer to break through any obstacle.",
            ),
        )


class TradeResult(BaseModel):
    player_name: Optional[str]
    player_inventory: Optional[List[Item]]
    player_bought: Optional[List[Item]]
    player_sold: Optional[List[Item]]
    player_gold_delta: Optional[int]
    player_gold: Optional[int]
    counterparty_name: Optional[str]

    error_message: Optional[str]
