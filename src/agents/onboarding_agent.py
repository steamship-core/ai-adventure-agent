from steamship import Block, MimeTypes, Tag
from steamship.agents.schema import Action, AgentContext
from steamship.agents.schema.action import FinishAction

from generators.generator_context_utils import get_image_generator, get_music_generator
from schema.characters import HumanCharacter
from schema.game_state import GameState
from utils.context_utils import (
    RunNextAgentException,
    await_ask,
    get_game_state,
    get_story_text_generator,
    save_game_state,
)
from utils.interruptible_python_agent import InterruptiblePythonAgent
from utils.moderation_utils import mark_block_as_excluded
from utils.tags import CampTag, CharacterTag, StoryContextTag, TagKindExtensions


def _is_allowed_by_moderation(user_input: str, context: AgentContext) -> bool:
    generator = get_story_text_generator(context)
    try:
        task = generator.generate(text=user_input)
        task.wait()
        return True
    except Exception as e:
        if "flagged" in str(e):
            return False
        return True


class OnboardingAgent(InterruptiblePythonAgent):
    """Implements the flow to onboared a new player.

    - For pure chat users, this is essential.
    - For web users, this is not necessary, as the website will provide this information via API.

    This flow uses checks against the game_state object to fast-forward through this logic in such that only
    the missing pieces of information are asked of the user in either chat or web mode.
    """

    def run(self, context: AgentContext) -> Action:  # noqa: C901
        game_state: GameState = get_game_state(context)
        player: HumanCharacter = game_state.player

        if not player.name:
            player.name = await_ask("What is your character's name?", context)
            if not _is_allowed_by_moderation(player.name, context):
                msgs = context.chat_history.messages
                for m in msgs:
                    if m.text == player.name:
                        mark_block_as_excluded(m)
                player.name = None
                save_game_state(game_state, context)
                raise RunNextAgentException(
                    FinishAction(
                        output=[
                            Block(
                                text="Your player name was flagged by the game's moderation engine. "
                                "Please select another name."
                            )
                        ]
                    )
                )
            save_game_state(game_state, context)

        if not player.background:
            player.background = await_ask(
                f"What is {player.name}'s backstory?", context
            )
            if not _is_allowed_by_moderation(player.background, context):
                msgs = context.chat_history.messages
                for m in msgs:
                    if m.text == player.background:
                        mark_block_as_excluded(m)
                player.background = None
                save_game_state(game_state, context)
                RunNextAgentException(
                    FinishAction(
                        output=[
                            Block(
                                text="Your player's background was flagged by the game's moderation engine. Please provide another."
                            )
                        ]
                    )
                )
            save_game_state(game_state, context)

        if not player.description:
            player.description = await_ask(
                f"What is {player.name}'s physical description?", context
            )
            if not _is_allowed_by_moderation(player.description, context):
                msgs = context.chat_history.messages
                for m in msgs:
                    if m.text == player.description:
                        mark_block_as_excluded(m)
                player.description = None
                save_game_state(game_state, context)
                raise RunNextAgentException(
                    FinishAction(
                        output=[
                            Block(
                                text="Your player's description was flagged by the game's moderation engine. Please provide another."
                            )
                        ]
                    )
                )
            save_game_state(game_state, context)

        if not game_state.image_generation_requested():
            if image_gen := get_image_generator(context):
                task = image_gen.request_profile_image_generation(context=context)
                character_image_block = task.wait().blocks[0]
                context.chat_history.file.refresh()
                game_state.player.profile_image_url = character_image_block.raw_data_url
                game_state.profile_image_url = character_image_block.raw_data_url
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
            if not _is_allowed_by_moderation(player.motivation, context):
                msgs = context.chat_history.messages
                for m in msgs:
                    if m.text == player.motivation:
                        mark_block_as_excluded(m)
                player.motivation = None
                save_game_state(game_state, context)
                raise RunNextAgentException(
                    FinishAction(
                        output=[
                            Block(
                                text="Your player's motivation was flagged by the game's moderation engine. Please provide another."
                            )
                        ]
                    )
                )
            save_game_state(game_state, context)

        if not game_state.genre:
            game_state.genre = await_ask(
                "What is the genre of the story (Adventure, Fantasy, Thriller, Sci-Fi)?",
                context,
            )
            if not _is_allowed_by_moderation(game_state.genre, context):
                msgs = context.chat_history.messages
                for m in msgs:
                    if m.text == game_state.genre:
                        mark_block_as_excluded(m)
                game_state.genre = None
                save_game_state(game_state, context)
                raise RunNextAgentException(
                    FinishAction(
                        output=[
                            Block(
                                text="Your genre was flagged by the game's moderation engine. Please provide another genre."
                            )
                        ]
                    )
                )
            save_game_state(game_state, context)

        if not game_state.tone:
            game_state.tone = await_ask(
                "What is the tone of the story (Hollywood style, Dark, Funny, Romantic)?",
                context,
            )
            if not _is_allowed_by_moderation(game_state.tone, context):
                msgs = context.chat_history.messages
                for m in msgs:
                    if m.text == game_state.genre:
                        mark_block_as_excluded(m)
                game_state.tone = None
                save_game_state(game_state, context)
                raise RunNextAgentException(
                    FinishAction(
                        output=[
                            Block(
                                text="Your tone was flagged by the game's moderation engine. Please provide another tone."
                            )
                        ]
                    )
                )
            save_game_state(game_state, context)

        if not game_state.camp_image_requested() and (
            game_state.tone and game_state.genre
        ):
            if image_gen := get_image_generator(context):
                task = image_gen.request_camp_image_generation(context=context)
                camp_image_block = task.wait().blocks[0]
                context.chat_history.file.refresh()
                game_state.camp.image_block_url = camp_image_block.raw_data_url
                save_game_state(game_state, context)

        if not game_state.camp_audio_requested() and (
            game_state.tone and game_state.genre
        ):
            if music_gen := get_music_generator(context):
                task = music_gen.request_camp_music_generation(context=context)
                camp_audio_block = task.wait().blocks[0]
                context.chat_history.file.refresh()
                game_state.camp.audio_block_url = camp_audio_block.raw_data_url
                save_game_state(game_state, context)

        if not game_state.chat_history_for_onboarding_complete:
            # TODO: We could save a lot of round trips by appending all these blocks at once.
            context.chat_history.append_system_message(
                text=f"The character's name is {player.name}",
                tags=[Tag(kind=TagKindExtensions.CHARACTER, name=CharacterTag.NAME)],
            )
            context.chat_history.append_system_message(
                text=f"{player.name}'s backstory is: {player.background}",
                tags=[
                    Tag(kind=TagKindExtensions.CHARACTER, name=CharacterTag.BACKGROUND)
                ],
            )
            context.chat_history.append_system_message(
                text=f"{player.name}'s motivation is: {player.motivation}",
                tags=[
                    Tag(kind=TagKindExtensions.CHARACTER, name=CharacterTag.MOTIVATION)
                ],
            )
            context.chat_history.append_system_message(
                text=f"{player.name}'s physical description is: {player.description}",
                tags=[
                    Tag(kind=TagKindExtensions.CHARACTER, name=CharacterTag.DESCRIPTION)
                ],
            )
            context.chat_history.append_system_message(
                text=f"The genre of the story is: {game_state.genre}",
                tags=[
                    Tag(
                        kind=TagKindExtensions.STORY_CONTEXT, name=StoryContextTag.GENRE
                    )
                ],
            )
            context.chat_history.append_system_message(
                text=f"The tone of the story is: {game_state.tone}",
                tags=[
                    Tag(kind=TagKindExtensions.STORY_CONTEXT, name=StoryContextTag.TONE)
                ],
            )
            game_state.chat_history_for_onboarding_complete = True
            save_game_state(game_state, context)

        if not game_state.camp_image_requested() and (
            game_state.tone and game_state.genre
        ):
            if image_gen := get_image_generator(context):
                task = image_gen.request_camp_image_generation(context=context)
                context.chat_history.file.refresh()
                camp_image_block = task.wait().blocks[0]
                game_state.camp.image_block_url = camp_image_block.raw_data_url
                save_game_state(game_state, context)

        if not game_state.camp_audio_requested() and (
            game_state.tone and game_state.genre
        ):
            if music_gen := get_music_generator(context):
                task = music_gen.request_camp_music_generation(context=context)
                context.chat_history.file.refresh()
                camp_audio_block = task.wait().blocks[0]
                game_state.camp.audio_block_url = camp_audio_block.raw_data_url
                save_game_state(game_state, context)

        if not game_state.chat_history_for_onboarding_complete:
            # TODO: We could save a lot of round trips by appending all these blocks at once.
            context.chat_history.append_system_message(
                text=f"The character's name is {player.name}",
                tags=[Tag(kind=TagKindExtensions.CHARACTER, name=CharacterTag.NAME)],
            )
            context.chat_history.append_system_message(
                text=f"{player.name}'s backstory is: {player.background}",
                tags=[
                    Tag(kind=TagKindExtensions.CHARACTER, name=CharacterTag.BACKGROUND)
                ],
            )
            context.chat_history.append_system_message(
                text=f"{player.name}'s motivation is: {player.motivation}",
                tags=[
                    Tag(kind=TagKindExtensions.CHARACTER, name=CharacterTag.MOTIVATION)
                ],
            )
            context.chat_history.append_system_message(
                text=f"{player.name}'s physical description is: {player.description}",
                tags=[
                    Tag(kind=TagKindExtensions.CHARACTER, name=CharacterTag.DESCRIPTION)
                ],
            )
            context.chat_history.append_system_message(
                text=f"The genre of the story is: {game_state.genre}",
                tags=[
                    Tag(
                        kind=TagKindExtensions.STORY_CONTEXT, name=StoryContextTag.GENRE
                    )
                ],
            )
            context.chat_history.append_system_message(
                text=f"The tone of the story is: {game_state.tone}",
                tags=[
                    Tag(kind=TagKindExtensions.STORY_CONTEXT, name=StoryContextTag.TONE)
                ],
            )
            game_state.chat_history_for_onboarding_complete = True
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
