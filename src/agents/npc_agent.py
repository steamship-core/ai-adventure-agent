from steamship import SteamshipError
from steamship.agents.functional import FunctionsBasedAgent
from steamship.agents.schema import Action, AgentContext
from steamship.agents.schema.message_selectors import MessageWindowMessageSelector

from schema.characters import NpcCharacter
from schema.game_state import GameState
from tools.end_conversation_tool import EndConversationTool
from utils.context_utils import get_current_conversant, get_game_state


class NpcAgent(FunctionsBasedAgent):
    """Agent to conduct a conversation with the player as an NPC.

    Players can converse with NPCs while at camp in between quests. Whether a player is in conversation is marked
    by the `game_state.in_conversation_with` field -- that will cause this agent to become active.

    This agent loads the profile of the NPC being conversed with and conducts it.

    There is a single tool: EndConversationTool.

    If buying or selling items was possible, those would be tools here as well.
    """

    PROMPT = "Tell the user that a personality was not yet loaded. Do not have any other conversation."

    def __init__(self, **kwargs):
        super().__init__(
            tools=[EndConversationTool()],
            message_selector=MessageWindowMessageSelector(k=10),
            **kwargs,
        )

    def set_prompt(self, game_state: GameState, npc: NpcCharacter):

        self.PROMPT = f"""You a script writer, imaging yourself as the character {npc.name} in a story.

The story describes your character as: {npc.description}
The story describes your character's background as: {npc.background}
The story describes your character's motivation as: {npc.motivation}

The story's theme is: {game_state.theme}
The story's tone is: {game_state.tone}

Respond to the chat with only dialogue that character would say - no more. Speak as a character in a story would: immersed in the scene, assuming the person you are speaking with shares similar knowledge.

Don't speak like an assistant (how can I assist you?). Instead, speak like a familiar person, as your character would.

NOTE: Some functions return images, video, and audio files. These multimedia files will be represented in messages as
UUIDs for Steamship Blocks. When responding directly to a user, you SHOULD print the Steamship Blocks for the images,
video, or audio as follows: `Block(UUID for the block)`.

Example response for a request that generated an image:
Here is the image you requested: Block(288A2CA1-4753-4298-9716-53C1E42B726B).

Only use the functions you have been provided with. Do not make up functions. If the user wants to go on a quest, function which ends the conversation.
"""

    def next_action(self, context: AgentContext) -> Action:
        # Switch the history to the new conversant
        npc = get_current_conversant(context)

        if not npc:
            raise SteamshipError(
                message="Player is in conversation with someone but unable to find their data record."
            )

        # Set the prompt to this NPC
        game_state = get_game_state(context)
        self.set_prompt(game_state, npc)
        return super().next_action(context)
