from pydantic import BaseModel, Field

class UserSettings(BaseModel):
  """Settings for a user of the game."""
  name: str = Field(description="The name of the character.")
  background: str = Field(description="The background of the character.")
  inventory: str = Field(description="The inventory of the character.")
  motivation: str = Field(description="The motivation of the character.")
  tone: str = Field(description="The tone of the story being told.")
  mission_summaries: List[str] = Field(description="The missions that the character has been on.")