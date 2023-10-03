from pydantic import BaseModel, Field
from typing import List, Optional
from steamship import Steamship, PluginInstance, Workspace, Block
from steamship.agents.schema import ChatHistory
from pydantic import BaseModel, Field
import uuid

class UserSettings(BaseModel):
  """Settings for a user of the game."""
  name: Optional[str] = Field(description="The name of the character.")
  description: Optional[str] = Field(description="The description of the character.")
  background: Optional[str] = Field(description="The background of the character.")
  inventory: Optional[str] = Field(description="The inventory of the character.")
  motivation: Optional[str] = Field(description="The motivation of the character.")
  tone: Optional[str] = Field(description="The tone of the story being told.")
  mission_summaries: List[str] = Field([], description="The missions that the character has been on.")