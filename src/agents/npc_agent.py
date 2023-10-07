from steamship import SteamshipError
from steamship.agents.functional import FunctionsBasedAgent
from steamship.agents.schema import Action, AgentContext
from steamship.agents.schema.message_selectors import MessageWindowMessageSelector

from context_utils import get_user_settings, switch_history_to_current_conversant
from schema.characters import NpcCharacter
from schema.user_settings import UserSettings
from tools.end_conversation_tool import EndConversationTool


class NpcAgent(FunctionsBasedAgent):
    """Agent to conduct a conversation with the player as an NPC.

    Players can converse with NPCs while at camp in between quests. Whether a player is in conversation is marked
    by the `user_settings.in_conversation_with` field -- that will cause this agent to become active.

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

    def set_prompt(self, user_settings: UserSettings, npc: NpcCharacter):

        self.PROMPT = f"""You a script writer, imaging yourself as the character {npc.name} in a story.

The story describes your character as: {npc.description}
The story describes your character's background as: {npc.background}

The story's theme is: {user_settings.theme}
The story's tone is: {user_settings.tone}

Respond to the chat with only dialogue that character would say - no more. Speak as a character in a story would: immersed in the scene, assuming the person you are speaking with shares similar knowledge.
"""

    def next_action(self, context: AgentContext) -> Action:
        # Switch the history to the new conversant
        npc = switch_history_to_current_conversant(context)

        if not npc:
            raise SteamshipError(
                message="Player is in conversation with someone but unable to find their data record."
            )

        # Set the prompt to this NPC
        user_settings = get_user_settings(context)
        self.set_prompt(user_settings, npc)
        return super().next_action(context)
