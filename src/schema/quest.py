from typing import List, Optional

from pydantic import BaseModel, Field

from schema.characters import Item


class QuestLocation(BaseModel):
    name: str = Field(description="Name of the quest location")
    description: str = Field(description="Description of the location")


class QuestObstacle(BaseModel):
    obstacle_type: str = Field(description="summary of obstacle type")
    obstacle_description: str = Field(description="full text description of the obstacle")
    block_indices: Optional[List[int]] = Field(default=[])


class QuestDescription(BaseModel):
    """The sketch of a quest the user will go on"""

    goal: str = Field(description="The goal of the quest")

    location: str = Field(description="The location of the quest")


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

    # For managing the back-and-forth
    sent_intro: Optional[bool] = Field(
        False, description="Whether the intro of the quest was sent to the user."
    )

    num_problems_to_encounter: int = Field(
        default=3,
        description="How many problems will the user encounter during the quest?",
    )

    user_problem_solutions: Optional[List[str]] = Field(
        default_factory=list, description="The user's solutions to the problems."
    )
    sent_outro: Optional[bool] = Field(
        False, description="Whether the outro of the quest was sent to the user."
    )

    goal: str = Field(description="point of quest")
    location: QuestLocation = Field(description="Location of the quest")
    obstacles: List[QuestObstacle] = Field(default=[], description="obstacles encountered in this quest")
    current_text_summary: Optional[str] = Field(default=None, description="used to store information on current state in case the need arises to compress history")
    difficulty: Optional[int] = Field(default=1, lt=10, ge=0)
    intro_block_index_in_file: Optional[int] = Field(description="...")

    # Output Fields
    image_url: Optional[str] = Field(
        None, description="An image of this quest generated afterwards by AI."
    )
    text_summary: Optional[str] = Field(
        None, description="A summary of the quest generated afterwards."
    )
    new_items: Optional[List[Item]] = Field(
        None, description="Any new items the player got while on the quest."
    )
    rank_delta: Optional[int] = Field(
        1, description="The change in rank that resulted from this quest."
    )
    gold_delta: Optional[int] = Field(
        25, description="The change in gold that resulted from this quest."
    )
    energy_delta: Optional[int] = Field(
        -10, description="The change in energy that resulted from this quest."
    )
    completed_timestamp: Optional[str] = Field(
        None, description="The timestamp at which the quest was completed"
    )

    # TODO(dougreid): cleanup
    social_media_summary: Optional[str] = Field(
        None, description="A social-media friendly summary"
    )
