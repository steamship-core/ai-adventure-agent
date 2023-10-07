from steamship.agents.schema import Action, AgentContext
from steamship.agents.schema.action import FinishAction

from tools.end_quest_tool import EndQuestTool
from utils.context_utils import get_game_state
from utils.generation_utils import (
    send_background_image,
    send_background_music,
    send_story_generation,
)
from utils.interruptible_python_agent import InterruptiblePythonAgent
from utils.script import GameChatHistory


class QuestAgent(InterruptiblePythonAgent):
    """
    The quest agent goes on a quest!

    HOW THIS AGENT IS ACTIVATED
    ===========================

    The game log defers to this agent when `game_state.current_quest` is not None.

    The `game_state.current_quest` argument matches `game_state.quests[].name` and is used to provide the
    Quest object to this agent at construction time so that it has a handle on where to load/store state.

    WHAT CAUSES THAT ACTIVATION TO HAPPEN
    =====================================

    The `use_settings.current_quest` string is set to not-None when the following things happen:

    - POST /start_quest (See the quest_mixin)
    - maybe later: The Camp Agent runs the Start Quest Tool

    It can be slotted into as a state machine sub-agent by the overall agent.
    """

    def run(self, context: AgentContext) -> Action:
        """
        It could go in a tool, but that doesn't feel necessary.. there are some other spots where tools feel very
        well fit, but this might be better left open-ended so we can stop/start things as we like.
        """

        # Load the main things we're working with. These can modified and the save_game_state called at any time
        game_state = get_game_state(context)
        # player = game_state.player
        # quest = get_current_quest(context)

        # if not purpose:
        #     logging.info(
        #         "No purpose for the quest was given, so inventing one..",
        #         extra={
        #             AgentLogging.IS_MESSAGE: True,
        #             AgentLogging.MESSAGE_TYPE: AgentLogging.THOUGHT,
        #             AgentLogging.MESSAGE_AUTHOR: AgentLogging.TOOL,
        #             AgentLogging.TOOL_NAME: self.name,
        #         },
        #     )
        #
        #     # TODO: Incorporate character information.
        #     task = generator.generate(text="What is a storybook quest one might go on?")
        #     task.wait()
        #     purpose = task.output.blocks[0].text
        #
        # task = generator.generate(
        #     text=f"What is a short, movie-title name for a storybook chapter/quest with this purpose: {purpose}"
        # )
        # task.wait()
        # name = task.output.blocks[0].text
        #
        # logging.info(
        #     f"Naming this quest: {name}",
        #     extra={
        #         AgentLogging.IS_MESSAGE: True,
        #         AgentLogging.MESSAGE_TYPE: AgentLogging.THOUGHT,
        #         AgentLogging.MESSAGE_AUTHOR: AgentLogging.TOOL,
        #         AgentLogging.TOOL_NAME: self.name,
        #     },
        # )
        #
        # quest = Quest(name=name, originating_string=purpose, chat_file_id=f"quest-{uuid.uuid4()}")
        #
        # # Create a Chat History for it.
        # logging.info(
        #     "Creating a new chat history and seeding it with information...",
        #     extra={
        #         AgentLogging.IS_MESSAGE: True,
        #         AgentLogging.MESSAGE_TYPE: AgentLogging.THOUGHT,
        #         AgentLogging.MESSAGE_AUTHOR: AgentLogging.TOOL,
        #         AgentLogging.TOOL_NAME: self.name,
        #     },
        # )

        script = GameChatHistory(context.chat_history)
        _ = script.generate_story(
            f"Like the narrator of a movie, explain that {game_state.player.name} is embarking on a quest. Speak briefly. Use only a few sentences.",
            context,
        )

        # TODO: How can these be emitted in a way that is both streaming friendly and sync-agent friendly?
        # THOUGHT: We might need to throw sync under the bus so that streaming can thrive

        # Note:
        #    We don't generate directly into the ChatHistory file because we can't yet add the right tags along

        send_background_music(prompt="Guitar music", context=context)
        send_background_image(prompt="In a deep, dark forest", context=context)
        send_story_generation(
            f"{game_state.player.name} it about to go on a mission. Describe the first few things they do in a few sentences",
            context=context,
        )

        script = GameChatHistory(context.chat_history)

        story_part_1 = script.generate_story(
            context,
        )

        script.generate_narration(story_part_1, context)

        script = GameChatHistory(context.chat_history)
        story_part_2 = script.generate_story(
            f"How does this mission end? {game_state.player.name} should not yet achieve their overall goal of {game_state.player.motivation}",
            context,
        )
        script.generate_narration(story_part_2, context)

        blocks = EndQuestTool().run([], context)
        return FinishAction(output=blocks)
