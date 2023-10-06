from steamship.agents.functional import FunctionsBasedAgent
from steamship.agents.schema import Action, AgentContext

from mixins.user_settings import UserSettings
from schema.characters import NpcCharacter


class NpcAgent(FunctionsBasedAgent):
    """The NPC Agent provides responses from an NPC.

    CONSIDER: This feels like a straight personality generation agent but has some sort of exit hatch.
    """

    PROMPT = ""

    user_settings: UserSettings
    character: NpcCharacter

    def set_prompt(self):
        self.PROMPT = f"""You a script writer, imaging yourself as the character {self.character.name} in a story.

The story describes your character as: {self.character.description}
The story describes your character's background as: {self.character.background}

The story's theme is: {self.user_settings.theme}
The story's tone is: {self.user_settings.tone}

Respond to the chat with only dialogue that character would say - no more. Speak as a character in a story would: immersed in the scene, assuming the person you are speaking with shares similar knowledge.
"""

    def next_action(self, context: AgentContext) -> Action:
        self.set_prompt()
        return super().next_action(context)
