from typing import List

from steamship import Block
from steamship.agents.functional import FunctionsBasedAgent
from steamship.agents.schema import AgentContext
from steamship.agents.schema.message_selectors import MessageWindowMessageSelector

from schema.game_state import GameState
from tools.start_quest_tool import StartQuestTool
from utils.context_utils import get_game_state
from utils.moderation_utils import is_block_excluded


class NonExcludedMessageWindowSelector(MessageWindowMessageSelector):
    def get_messages(self, messages: List[Block]) -> List[Block]:
        # choice here: if the user has been submitting a bunch of problematic conversation
        #              then we are ok "forgetting" the distant context. so, we can trim from
        #              the discovered window, rather than first filtering and then selecting
        #              via the window.
        context_messages = super().get_messages(messages)
        return [msg for msg in context_messages if not is_block_excluded(msg)]


class CampAgent(FunctionsBasedAgent):
    """The Camp Agent is in charge of your experience while at camp.

    A player is at camp while they are not on a quest.

    CONSIDER: This feels like a FunctionCallingAgent
    """

    PROMPT = ""

    def __init__(self, **kwargs):
        super().__init__(
            tools=[StartQuestTool()],  # , StartConversationTool()],
            message_selector=NonExcludedMessageWindowSelector(k=10),
            **kwargs,
        )

    def next_action(self, context: AgentContext):
        """Choose the next action.

        We defer to the superclass but have to dynamically set our prompt with the context."""
        game_state = get_game_state(context)
        self.set_prompt(game_state)
        return super().next_action(context)

    def set_prompt(self, game_state: GameState):
        npcs = []
        if game_state and game_state.camp and game_state.camp.npcs:
            npcs = game_state.camp.npcs

        if npcs:
            camp_crew = "Your camp has the following people:\n\n" + "\n".join(
                [f"- {npc.name}" for npc in npcs or []]
            )
        else:
            camp_crew = "Nobody is currently with you at camp."

        self.PROMPT = f"""You are a game engine which helps users make a choice of option.

They only have two options to choose between:

1) Go on a quest
2) Talk to someone in the camp

{camp_crew}

If they're not asking to go on a quest or talk to someone in a camp, greet them by name, {game_state.player.name}, and concisely entertain casual chit-chat but remind them of what options are at their disposal.

Don't speak like an assistant (how can I assist you?). Instead, speak like a familiar person.

NOTE: Some functions return images, video, and audio files. These multimedia files will be represented in messages as
UUIDs for Steamship Blocks. When responding directly to a user, you SHOULD print the Steamship Blocks for the images,
video, or audio as follows: `Block(UUID for the block)`.

Example response for a request that generated an image:
Here is the image you requested: Block(288A2CA1-4753-4298-9716-53C1E42B726B).

Only use the functions you have been provided with."""
