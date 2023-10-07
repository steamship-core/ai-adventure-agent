import logging

from steamship.agents.schema import Action, Agent, AgentContext
from steamship.agents.schema.action import FinishAction

from context_utils import get_user_settings
from schema.user_settings import UserSettings
from script import Script
from tools.end_quest_tool import EndQuestTool


class QuestAgent(Agent):
    """
    The quest agent goes on a quest!

    HOW THIS AGENT IS ACTIVATED
    ===========================

    The game log defers to this agent when `user_settings.current_quest` is not None.

    The `user_settings.current_quest` argument matches `user_settings.quests[].name` and is used to provide the
    Quest object to this agent at construction time so that it has a handle on where to load/store state.

    WHAT CAUSES THAT ACTIVATION TO HAPPEN
    =====================================

    The `use_settings.current_quest` string is set to not-None when the following things happen:

    - POST /start_quest (See the quest_mixin)
    - maybe later: The Camp Agent runs the Start Quest Tool

    It can be slotted into as a state machine sub-agent by the overall agent.
    """

    def run_quest(self, user_settings: UserSettings, context: AgentContext):
        """
        TODO: This is basically where the meat of the storytelling happens.

        It could go in a tool, but that doesn't feel necessary.. there are some other spots where tools feel very
        well fit, but this might be better left open-ended so we can stop/start things as we like.
        """
        script = Script(context.chat_history)
        _ = script.generate_story(
            f"Like the narrator of a movie, explain that {user_settings.player.name} is embarking on a quest. Speak briefly. Use only a few sentences.",
            context,
        )

        # TODO: How can these be emitted in a way that is both streaming friendly and sync-agent friendly?
        # THOUGHT: We might need to throw sync under the bus so that streaming can thrive
        script.generate_background_music("Soft guitar music playing", context)

        script.generate_background_image("A picture of a forest", context)

        script = Script(context.chat_history)

        story_part_1 = script.generate_story(
            f"{user_settings.player.name} it about to go on a mission. Describe the first few things they do in a few sentences",
            context,
        )

        script.generate_narration(story_part_1, context)

        script = Script(context.chat_history)
        story_part_2 = script.generate_story(
            f"How does this mission end? {user_settings.player.name} should not yet achieve their overall goal of {user_settings.player.motivation}",
            context,
        )
        script.generate_narration(story_part_2, context)

    def next_action(self, context: AgentContext) -> Action:
        user_settings = get_user_settings(context)
        try:
            self.run_quest(user_settings, context)
            blocks = EndQuestTool().run([], context)
            return FinishAction(output=blocks)
        except BaseException as e:
            logging.exception(e)
