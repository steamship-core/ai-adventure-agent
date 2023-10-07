from steamship import Block, MimeTypes
from steamship.agents.schema import Action, Agent, AgentContext
from steamship.agents.schema.action import FinishAction

from api_endpoints.user_settings import UserSettings
from context_utils import get_current_quest, get_user_settings
from schema.objects import Item
from schema.quest_settings import Quest
from script import Script


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

    def begin_quest(self, user_settings: UserSettings, context: AgentContext):
        """

        CONSIDER: Should this be a Tool?
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

    def finish_quest(self, user_settings: UserSettings, context: AgentContext):
        """

        CONSIDER: Should this be a Tool?
        """

        script = Script(context.chat_history)

        story_part_2 = script.generate_story(
            f"How does this mission end? {user_settings.player.name} should not yet achieve their overall goal of {user_settings.player.motivation}",
            context,
        )

        script.generate_narration(story_part_2, context)

    def release_agent(
        self, user_settings: UserSettings, quest: Quest, context: AgentContext
    ):
        """Does final summarizing activities.

        TODO: Inform the controlling agent that our work is done.
        CONSIDER: Could this be async?
        """
        script = Script(context.chat_history)

        quest.text_summary = "[TODO] Replace this summary with a generated one."
        quest.new_items = [
            Item(name="[TODO] Replace this with an item the player found.")
        ]
        quest.rank_delta = 1

        # TODO: Save quest
        script.end_scene(quest, context)

    def next_action(self, context: AgentContext) -> Action:
        user_settings = get_user_settings(context)
        quest = get_current_quest(context)

        try:
            self.begin_quest(user_settings, context)
            self.finish_quest(user_settings, context)
            self.release_agent(user_settings, quest, context)

            # CONCLUDE STORY
            """
            TODO
            Block is of type END SCENE and contains JSON with the summary.

            - how much gold
            - what items
            - summary of the journey

            Every Quest is a different chat history.
            - There would be a quest log button somewhere.
            - In that quest log.
            """

            final_block = Block(text="The quest is over.", mime_type=MimeTypes.MKD)
            return FinishAction(output=[final_block])
        except BaseException as e:
            print(e)
