from steamship import Block, MimeTypes
from steamship.agents.schema import Action, AgentContext
from steamship.agents.schema.action import FinishAction

from schema.characters import HumanCharacter
from schema.game_state import GameState
from schema.objects import Item
from utils.context_utils import (
    RunNextAgentException,
    await_ask,
    get_game_state,
    save_game_state,
)
from utils.interruptible_python_agent import InterruptiblePythonAgent


class OnboardingAgent(InterruptiblePythonAgent):
    """Implements the flow to onboared a new player.

    - For pure chat users, this is essential.
    - For web users, this is not necessary, as the website will provide this information via API.

    This flow uses checks against the game_state object to fast-forward through this logic in such that only
    the missing pieces of information are asked of the user in either chat or web mode.
    """

    def run(self, context: AgentContext) -> Action:
        game_state: GameState = get_game_state(context)
        player: HumanCharacter = game_state.player

        if not player.name:
            player.name = await_ask("What is your character's name?", context)
            save_game_state(game_state, context)

        if not player.background:
            player.background = await_ask(
                f"What is {player.name}'s backstory?", context
            )
            save_game_state(game_state, context)

        # TODO: How can we do something like this:
        # if not player.image_generation:
        #    player.image_generation = generate(..)
        #    save_game_state(game_state, context)
        #
        # But have that operation:
        #    1) NOT WAIT!! for the generation to complete!
        #    2) Result in game_state having data that contains, without ANY additional requirements by the web client,
        #       the URL of the generation
        #    3) Some kind of notification.. e.g. on the chat history, etc, of the asset being ready
        #
        # Ideally as soon as we:
        #    1) Know the description, but
        #    2) Realize we haven't made a character image
        #
        # We just kick off a generation loop.
        #

        if not player.inventory:
            name = await_ask(f"What is {player.name}'s starting item?", context)
            if player.inventory is None:
                player.inventory = []
            player.inventory.append(Item(name=name))
            save_game_state(game_state, context)

        if not player.motivation:
            player.motivation = await_ask(
                f"What is {player.name} motivated to achieve?", context
            )
            save_game_state(game_state, context)

        if not game_state.genre:
            game_state.genre = await_ask(
                "What is the genre of the story (Adventure, Fantasy, Thriller, Sci-Fi)?",
                context,
            )
            save_game_state(game_state, context)

        if not game_state.tone:
            game_state.tone = await_ask(
                "What is the tone of the story (Hollywood style, Dark, Funny, Romantic)?",
                context,
            )
            save_game_state(game_state, context)

        raise RunNextAgentException(
            action=FinishAction(
                input=[
                    Block(
                        text=f"{player.name} arrives at camp.",
                        mime_type=MimeTypes.MKD,
                    )
                ],
                output=[
                    Block(
                        text=f"{player.name}! Let's get you to camp! This is where all your quests begin from.",
                        mime_type=MimeTypes.MKD,
                    )
                ],
            )
        )
