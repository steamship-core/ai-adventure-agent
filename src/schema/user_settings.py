from typing import List, Optional

from pydantic import BaseModel, Field


class UserSettings(BaseModel):
    """Settings for a user of the game."""

    name: Optional[str] = Field(
        "Leroy Jenkins", description="The name of the character."
    )
    description: Optional[str] = Field(
        "A Programmer", description="The description of the character."
    )
    background: Optional[str] = Field(
        "From a small town", description="The background of the character."
    )
    inventory: Optional[str] = Field(
        "A keyboard", description="The inventory of the character."
    )
    motivation: Optional[str] = Field(
        "Wnats to be Bill Gates", description="The motivation of the character."
    )
    tone: Optional[str] = Field(
        "Silly", description="The tone of the story being told."
    )
    mission_summaries: List[str] = Field(
        [], description="The missions that the character has been on."
    )

    def is_character_completed(self) -> bool:
        """Return True if the character is completed."""
        return (
            self.name
            and self.background
            and self.inventory
            and self.motivation
            and self.tone
        )

        # TODO: return self.name and self.background and self.inventory and self.motivation and self.tone
        # Such that we interrupt and ask about these if they're not there.
        # Could we have some sort of BaseMode.set_with_question("field", "question") class?
