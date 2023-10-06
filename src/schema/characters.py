from typing import List, Optional

from pydantic import BaseModel, Field


class Item(BaseModel):
    name: Optional[str]
    description: Optional[str]
    is_one_time_use: Optional[bool]

    modifier: Optional[int]
    """Modifier is a placeholder for the future. The game settings can assigne int->String values like "mythic", etc."""

    picture_url: Optional[str]


class Character(BaseModel):
    name: Optional[str]

    description: Optional[str] = Field(
        "A Programmer", description="The description of the character."
    )
    background: Optional[str] = Field(
        "From a small town", description="The background of the character."
    )
    inventory: Optional[List[Item]] = Field(
        [], description="The inventory of the character."
    )
    motivation: Optional[str] = Field(
        "Wants to be Bill Gates", description="The motivation of the character."
    )


class NpcCharacter(Character):
    category: Optional[str] = Field(
        "conversational",
        description="The kind of NPC. Can be 'conversational' or 'merchant'",
    )
    disposition_toward_player: Optional[int] = Field(
        1,
        description="The disposition of the Npc toward the player. 1=Doesn't know you. 5=Knows you very well.",
    )


class Merchant(NpcCharacter):
    """Intent:
    - The Merchant appears in your camp after your second quest.
    - The Merchant updates items after each quest, the cost of the items scale with the player RANK. Higher rank is
      more expensive items.
    - If you buy, disposition goes up.
    - If you only sell, dispotition goes down. Or something?
    """

    pass


class TravelingMerchant(NpcCharacter):
    """Intent:
    - The TravelingMerchant only shows up if your RANK % 5 = 0.
    - They always have REALLY good stuff.
    """

    pass


class HumanCharacter(Character):
    rank: Optional[int] = Field(
        1, description="The rank of a player. Higher rank equals more power."
    )
    gold: Optional[int] = Field(
        0,
        description="The gold the player has. Gold can be used buy items from the Merchant. Gold is acquired by selling items to the Merchant and after every quest.",
    )
    energy: Optional[int] = Field(
        100,
        description="The energy the player has. Going on a quest requires and expends energy. This is the unit of monetization for the game.",
    )

    def is_character_completed(self) -> bool:
        """Return True if the character is completed."""
        return (
            self.name is not None
            and self.background is not None
            and self.inventory is not None
            and self.motivation is not None
        )

        # TODO: return self.name and self.background and self.inventory and self.motivation and self.tone
        # Such that we interrupt and ask about these if they're not there.
        # Could we have some sort of BaseMode.set_with_question("field", "question") class?
