class Quest(BaseModel):
  """Information about a quest."""
  description: str = Field(description="The description of the quest.")
  chat_history: ChatHistory = Field(description="The chat history of the quest.")



  def create_chat_history(self, user_settings: UserSettings):
      self.chat_history = ChatHistory.get_or_create(self.client, {"id": str(uuid.uuid4())})
      self.chat_history.append_system_message(
          f"We are writing a story about the adventure of a character named {user_settings.name}.")
      self.chat_history.append_system_message(f"{user_settings.name} has the following background: {user_settings.background}")
      self.chat_history.append_system_message(f"{user_settings.name} has the following things in their inventory: {user_settings.inventory}")
      self.chat_history.append_system_message(f"{user_settings.name}'s motivation is to {user_settings.motivation}")
      self.chat_history.append_system_message(f"The tone of this story is {user_settings.tone}")
      prepared_mission_summaries = '\n'.join(user_settings.mission_summaries)
      if len(self.mission_summaries) > 0:
          self.chat_history.append_system_message(f"{user_settings.name} has already been on previous missions: \n {prepared_mission_summaries}")
      return self.chat_history
