from typing import Optional

from pydantic import BaseModel, Field


class Location(BaseModel):
    """Where a character is in the world."""

    description: Optional[str] = Field(description="Description of the location.")
