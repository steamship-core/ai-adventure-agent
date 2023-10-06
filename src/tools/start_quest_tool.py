from typing import Any, List, Optional, Union

from steamship import Block, Task
from steamship.agents.schema import AgentContext, Tool

from context_utils import get_narration_generator
from mixins.user_settings import UserSettings
from schema.quest_settings import Quest


class StartQuestTool(Tool):
    """Starts a quest.

    Designed in a way that either an API call or an Agent can call it.
    """

    user_settings: UserSettings

    def __init__(self, user_settings: UserSettings, **kwargs):
        self.user_settings = user_settings
        kwargs["name"] = "StartQuestTool"
        kwargs[
            "agent_description"
        ] = "Use when the user wants to go on a quest. The input is the kind of quest, if provided. The output is the Quest Name"
        kwargs[
            "human_description"
        ] = "Tool to initiate a quest. Modifies the global state such that the next time the agent is contacted, it will be on a quets."

        # It always returns.. OK! Let's go!
        kwargs["is_final"] = True
        super().__init__(**kwargs)

    def create_quest(
        self,
        user_settings: UserSettings,
        context: AgentContext,
        purpose: Optional[str] = None,
    ) -> Quest:
        generator = get_narration_generator(context)

        if not purpose:
            # TODO: Incorporate character information.
            task = generator.generate(text="What is a storybook quest one might go on?")
            task.wait()
            purpose = task.output.blocks[0].text

        task = generator.generate(
            text=f"What is a short, movie-title name for a storybook chapter/quest with this purpose: {purpose}"
        )
        task.wait()
        name = task.output.blocks[0].text
        return Quest(name=name, user_input=purpose)

    def start_quest(
        self,
        user_settings: UserSettings,
        context: AgentContext,
        purpose: Optional[str] = None,
    ) -> Quest:
        """Creates and starts a new quest."""
        quest = self.create_quest(user_settings, context, purpose)
        if not user_settings.quests:
            user_settings.quests = []
        user_settings.quests.append(quest)
        user_settings.current_quest = quest.name
        user_settings.save(context.client)
        return quest

    def run(
        self, tool_input: List[Block], context: AgentContext
    ) -> Union[List[Block], Task[Any]]:
        purpose = None

        if tool_input:
            purpose = tool_input[0].text

        quest = self.start_quest(self.user_settings, context, purpose)
        return [Block(text=f"Starting quest... titled: {quest.name}")]
