import uuid
from typing import List, Optional

from pydantic import BaseModel, Field

from schema.characters import Item

# from schema.server_settings import SettingField


class QuestChallengeDescription(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    name: Optional[str] = Field(
        default="",
        description="Short name for the challenge",
    )

    description: Optional[str] = Field(
        default="",
        description="Description of the challenge",
    )


class QuestChallenge(QuestChallengeDescription):
    class Config:
        arbitrary_types_allowed = True

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="unique identifier for the challenge",
    )

    attempts: int = Field(
        default=0,
        description="Number of attempts at solution",
    )

    solution: Optional[str] = Field(
        default=None, description="User-provided solution to the challenge"
    )


class QuestDescription(BaseModel):
    """The sketch of a quest the user will go on"""

    class Config:
        arbitrary_types_allowed = True

    goal: str = Field(description="The goal of the quest")

    location: str = Field(description="The location of the quest")

    description: Optional[str] = Field(None, description="A description of the quest")

    other_information: Optional[str] = Field(
        None,
        description="Other information or instructions for the story of this quest, which will not be shown to the user.",
    )

    challenges: Optional[List[QuestChallengeDescription]] = Field(
        default=[],
        description="An ordered list of challenges that will be encountered on this quest.",
    )


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

    current_problem: Optional[str] = Field(
        default=None, description="The current problem in the quest"
    )

    sent_outro: Optional[bool] = Field(
        False, description="Whether the outro of the quest was sent to the user."
    )

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
    completed_success: Optional[bool] = Field(
        None,
        description="Whether the quest was completeed successfully (True) or unsuccessfully (False)",
    )

    # TODO(dougreid): cleanup
    social_media_summary: Optional[str] = Field(
        None, description="A social-media friendly summary"
    )

    challenges: Optional[List[QuestChallenge]] = Field(
        default=[],
        description="A list of challenges that MUST be encountered on this quest.",
    )

    def all_problems_solved(self) -> bool:
        if len(self.challenges) > 0:
            solved_challenges = sum([1 if x.solution else 0 for x in self.challenges])
            return solved_challenges == len(self.challenges)
        else:
            return len(self.user_problem_solutions) == self.num_problems_to_encounter

    def add_user_solution(self, user_solution: str):
        self.user_problem_solutions.append(user_solution)
        if len(self.challenges) > 0:
            solved_challenges = sum([1 if x.solution else 0 for x in self.challenges])
            if isinstance(solved_challenges, int) and solved_challenges < len(
                self.challenges
            ):
                self.challenges[solved_challenges].attempts = (
                    self.challenges[solved_challenges].attempts + 1
                )
                self.challenges[solved_challenges].solution = user_solution

    def rollback_solution(self):
        self.user_problem_solutions.pop()
        if len(self.challenges) > 0:
            solved_challenges = sum([1 if x.solution else 0 for x in self.challenges])
            if isinstance(solved_challenges, int):
                self.challenges[solved_challenges - 1].solution = None
