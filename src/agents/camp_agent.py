from steamship import Block, MimeTypes
from steamship.agents.schema import Action, Agent, AgentContext
from steamship.agents.schema.action import FinishAction

from mixins.user_settings import UserSettings


class CampAgent(Agent):
    """The Camp Agent is in charge of your experience while at camp.

    A player is at camp while they are not on a quest.

    CONSIDER: This feels like a FunctionCallingAgent
    """

    PROMPT = ""

    user_settings: UserSettings

    def set_prompt(self):
        npcs = self.user_settings.camp.npcs or []
        if npcs:
            camp_crew = "Your camp has the following people:\n\n" + "\n".join(
                [f"- {npc.name}" for npc in self.user_settings.camp.npcs or []]
            )
        else:
            camp_crew = "Nobody is currently with you at camp."

        self.PROMPT = f"""You a game engine which helps users make a choice of option.

They only have two options to choose between:

1) Go on a quest
2) Talk to someone in the camp

{camp_crew}

NOTE: Some functions return images, video, and audio files. These multimedia files will be represented in messages as
UUIDs for Steamship Blocks. When responding directly to a user, you SHOULD print the Steamship Blocks for the images,
video, or audio as follows: `Block(UUID for the block)`.

Example response for a request that generated an image:
Here is the image you requested: Block(288A2CA1-4753-4298-9716-53C1E42B726B).

Only use the functions you have been provided with."""

    def next_action(self, context: AgentContext) -> Action:
        self.set_prompt()
        return FinishAction(
            output=[
                Block(
                    text="You are at camp.",
                    mime_type=MimeTypes.MKD,
                )
            ]
        )
