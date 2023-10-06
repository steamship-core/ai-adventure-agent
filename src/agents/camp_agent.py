from steamship.agents.functional import FunctionsBasedAgent
from steamship.agents.schema import AgentContext
from steamship.agents.schema.message_selectors import MessageWindowMessageSelector

from context_utils import get_user_settings
from mixins.user_settings import UserSettings
from tools.start_quest_tool import StartQuestTool


class CampAgent(FunctionsBasedAgent):
    """The Camp Agent is in charge of your experience while at camp.

    A player is at camp while they are not on a quest.

    CONSIDER: This feels like a FunctionCallingAgent
    """

    PROMPT = ""

    def __init__(self, **kwargs):
        super().__init__(
            tools=[StartQuestTool()],
            message_selector=MessageWindowMessageSelector(k=10),
            **kwargs,
        )

    def next_action(self, context: AgentContext):
        """Choose the next action.

        We defer to the superclass but have to dynamically set our prompt with the context."""
        user_settings = get_user_settings(context)
        self.set_prompt(user_settings)
        return super().next_action(context)

    def set_prompt(self, user_settings: UserSettings):
        npcs = []
        if user_settings and user_settings.camp and user_settings.camp.npcs:
            npcs = user_settings.camp.npcs

        if npcs:
            camp_crew = "Your camp has the following people:\n\n" + "\n".join(
                [f"- {npc.name}" for npc in npcs or []]
            )
        else:
            camp_crew = "Nobody is currently with you at camp."

        self.PROMPT = f"""You a game engine which helps users make a choice of option.

They only have two options to choose between:

1) Go on a quest
2) Talk to someone in the camp

{camp_crew}

If they're not asking to go on a quest or talk to someone in a camp, greet them by name, {user_settings.player.name}, and concisely entertain casual chit-chat but remind them of what options are at their disposal.

Don't speak like an assistant (how can I assist you?). Instead, speak like a familiar person.

NOTE: Some functions return images, video, and audio files. These multimedia files will be represented in messages as
UUIDs for Steamship Blocks. When responding directly to a user, you SHOULD print the Steamship Blocks for the images,
video, or audio as follows: `Block(UUID for the block)`.

Example response for a request that generated an image:
Here is the image you requested: Block(288A2CA1-4753-4298-9716-53C1E42B726B).

Only use the functions you have been provided with."""
