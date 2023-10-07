import logging
from typing import Any, List, Optional, Union

from steamship import Block, Task
from steamship.agents.logging import AgentLogging
from steamship.agents.schema import AgentContext, Tool

from api_endpoints.user_settings import UserSettings
from context_utils import (
    get_story_text_generator,
    get_user_settings,
    save_user_settings,
)
from schema.quest_settings import Quest


class StartQuestTool(Tool):
    """Starts a quest.

    This Tool is meant to TRANSITION from one agent (the CAMP AGENT) to the next (THE QUEST AGENT). It does that
    by modifying state and returning.

    It can either be called by:
     - The CAMP AGENT (when in full-chat mode) -- see camp_agent.py
     - The WEB APP (when in web-mode, via api) -- see quest_mixin.py
    """

    def __init__(self, **kwargs):
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

    def start_quest(
        self,
        user_settings: UserSettings,
        context: AgentContext,
        purpose: Optional[str] = None,
    ) -> Quest:
        generator = get_story_text_generator(context)

        if not purpose:
            logging.info(
                "No purpose for the quest was given, so inventing one..",
                extra={
                    AgentLogging.IS_MESSAGE: True,
                    AgentLogging.MESSAGE_TYPE: AgentLogging.THOUGHT,
                    AgentLogging.MESSAGE_AUTHOR: AgentLogging.TOOL,
                    AgentLogging.TOOL_NAME: self.name,
                },
            )

            # TODO: Incorporate character information.
            task = generator.generate(text="What is a storybook quest one might go on?")
            task.wait()
            purpose = task.output.blocks[0].text

        task = generator.generate(
            text=f"What is a short, movie-title name for a storybook chapter/quest with this purpose: {purpose}"
        )
        task.wait()
        name = task.output.blocks[0].text

        logging.info(
            f"Naming this quest: {name}",
            extra={
                AgentLogging.IS_MESSAGE: True,
                AgentLogging.MESSAGE_TYPE: AgentLogging.THOUGHT,
                AgentLogging.MESSAGE_AUTHOR: AgentLogging.TOOL,
                AgentLogging.TOOL_NAME: self.name,
            },
        )

        quest = Quest(name=name, originating_string=purpose)

        if not user_settings.quests:
            user_settings.quests = []
        user_settings.quests.append(quest)
        user_settings.current_quest = quest.name

        # This saves it in a way that is both persistent (KV Store) and updates the context
        save_user_settings(user_settings, context)

        return Quest(name=name, user_input=purpose)

    def run(
        self, tool_input: List[Block], context: AgentContext
    ) -> Union[List[Block], Task[Any]]:
        purpose = None
        user_settings = get_user_settings(context)

        if tool_input:
            purpose = tool_input[0].text

        quest = self.start_quest(user_settings, context, purpose)
        return [Block(text=f"Starting quest... titled: {quest.name}")]
