from steamship import Block, MimeTypes, Tag
from steamship.agents.schema import Action, AgentContext
from steamship.agents.schema.action import FinishAction

from schema.characters import HumanCharacter
from schema.game_state import GameState
from schema.objects import Item
from utils.agent_service import _context_key_from_file
from utils.context_utils import (
    RunNextAgentException,
    await_ask,
    get_game_state,
    get_package_service,
    save_game_state,
)
from utils.interruptible_python_agent import InterruptiblePythonAgent
from utils.tags import CharacterTag, StoryContextTag, TagKindExtensions


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
            context.chat_history.append_system_message(
                text=f"The character's name is {player.name}",
                tags=[Tag(kind=TagKindExtensions.CHARACTER, name=CharacterTag.NAME)],
            )
            save_game_state(game_state, context)

        if not player.background:
            player.background = await_ask(
                f"What is {player.name}'s backstory?", context
            )
            context.chat_history.append_system_message(
                text=f"{player.name}'s backstory is: {player.background}",
                tags=[
                    Tag(kind=TagKindExtensions.CHARACTER, name=CharacterTag.BACKGROUND)
                ],
            )
            save_game_state(game_state, context)

        if not player.description:
            player.description = await_ask(
                f"What is {player.name}'s physical description?", context
            )
            context.chat_history.append_system_message(
                text=f"{player.name}'s physical description is: {player.description}",
                tags=[
                    Tag(kind=TagKindExtensions.CHARACTER, name=CharacterTag.DESCRIPTION)
                ],
            )
            save_game_state(game_state, context)

        if not game_state.image_generation_requested():
            # TODO: should this move to after tone/genre are set?
            svc = get_package_service(context=context)
            task = svc.invoke_later(
                method="generate_profile_image",
                arguments={
                    "context_id": _context_key_from_file(
                        key="id", file=context.chat_history.file
                    )
                },
            )
            game_state.profile_image_task = task
            save_game_state(game_state, context)

        if not player.inventory:
            # name = await_ask(f"What is {player.name}'s starting item?", context)
            if player.inventory is None:
                player.inventory = []
            # player.inventory.append(Item(name=name))
            save_game_state(game_state, context)

        if not player.motivation:
            player.motivation = await_ask(
                f"What is {player.name} motivated to achieve?", context
            )
            context.chat_history.append_system_message(
                text=f"{player.name}'s motivation is: {player.motivation}",
                tags=[
                    Tag(kind=TagKindExtensions.CHARACTER, name=CharacterTag.MOTIVATION)
                ],
            )
            save_game_state(game_state, context)

        if not game_state.genre:
            game_state.genre = await_ask(
                "What is the genre of the story (Adventure, Fantasy, Thriller, Sci-Fi)?",
                context,
            )
            context.chat_history.append_system_message(
                text=f"The genre of the story is: {game_state.genre}",
                tags=[
                    Tag(
                        kind=TagKindExtensions.STORY_CONTEXT, name=StoryContextTag.GENRE
                    )
                ],
            )
            save_game_state(game_state, context)

        if not game_state.tone:
            game_state.tone = await_ask(
                "What is the tone of the story (Hollywood style, Dark, Funny, Romantic)?",
                context,
            )
            context.chat_history.append_system_message(
                text=f"The tone of the story is: {game_state.tone}",
                tags=[
                    Tag(kind=TagKindExtensions.STORY_CONTEXT, name=StoryContextTag.TONE)
                ],
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
