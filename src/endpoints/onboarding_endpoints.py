import logging
from typing import Optional

from steamship import Steamship, SteamshipError
from steamship.agents.llms.openai import ChatOpenAI
from steamship.agents.service.agent_service import AgentService
from steamship.invocable import post
from steamship.invocable.package_mixin import PackageMixin

from agents.onboarding_agent import OnboardingAgent, _is_allowed_by_moderation
from generators.generator_context_utils import get_image_generator
from generators.utils import find_new_block
from schema.game_state import ActiveMode, GameState

# An instnace is a game instance.
from utils.context_utils import RunNextAgentException, get_game_state, save_game_state
from utils.generation_utils import generate_story_intro
from utils.tags import CharacterTag, TagKindExtensions


class OnboardingMixin(PackageMixin):
    """Provides endpoints for Onboarding."""

    agent_service: AgentService
    client: Steamship

    def __init__(self, client: Steamship, agent_service: AgentService):
        self.client = client
        self.agent_service = agent_service

    @post("/onboarding/character/name")
    def set_character_name(self, name: str, context_id: Optional[str] = None, **kwargs):
        context = self.agent_service.build_default_context(
            context_id=context_id, **kwargs
        )

        if not _is_allowed_by_moderation(name, context):
            raise SteamshipError(
                "Supplied 'name' was rejected by game's moderation filter. Please try again."
            )

        game_state = get_game_state(context)
        game_state.player.name = name
        save_game_state(game_state, context)

    @post("/onboarding/character/background")
    def set_character_background(
        self, background: str, context_id: Optional[str] = None, **kwargs
    ):
        context = self.agent_service.build_default_context(
            context_id=context_id, **kwargs
        )

        if not _is_allowed_by_moderation(background, context):
            raise SteamshipError(
                "Supplied 'background' was rejected by game's moderation filter. Please try again."
            )

        game_state = get_game_state(context)
        game_state.player.background = background
        save_game_state(game_state, context)

    @post("/onboarding/character/description")
    def set_character_description(
        self,
        description: str,
        update: Optional[bool] = True,
        context_id: Optional[str] = None,
        **kwargs,
    ):
        context = self.agent_service.build_default_context(
            context_id=context_id, **kwargs
        )

        if not _is_allowed_by_moderation(description, context):
            raise SteamshipError(
                "Supplied 'description' was rejected by game's moderation filter. Please try again."
            )

        game_state = get_game_state(context)
        game_state.player.description = description

        if game_state.player.description and game_state.player.name:
            if (not game_state.image_generation_requested()) or update:
                if image_gen := get_image_generator(context):
                    num_known_blocks = len(context.chat_history.file.blocks)
                    image_gen.request_profile_image_generation(context=context)
                    context.chat_history.file.refresh()
                    character_image_block = find_new_block(
                        file=context.chat_history.file,
                        num_known_blocks=num_known_blocks,
                        new_block_tag_kind=TagKindExtensions.CHARACTER,
                        new_block_tag_name=CharacterTag.IMAGE,
                    )
                    game_state.player.profile_image_url = (
                        character_image_block.raw_data_url
                    )
                    game_state.profile_image_url = character_image_block.raw_data_url
                    save_game_state(game_state, context)

        save_game_state(game_state, context)

    @post("/onboarding/character/motivation")
    def set_character_motivation(
        self, motivation: str, context_id: Optional[str] = None, **kwargs
    ):
        context = self.agent_service.build_default_context(
            context_id=context_id, **kwargs
        )

        if not _is_allowed_by_moderation(motivation, context):
            raise SteamshipError(
                "Supplied 'description' was rejected by game's moderation filter. Please try again."
            )

        game_state = get_game_state(context)
        game_state.player.motivation = motivation
        save_game_state(game_state, context)

    @post("/onboarding/game/tone")
    def set_game_tone(self, tone: str, context_id: Optional[str] = None, **kwargs):
        context = self.agent_service.build_default_context(
            context_id=context_id, **kwargs
        )

        if not _is_allowed_by_moderation(tone, context):
            raise SteamshipError(
                "Supplied 'tone' was rejected by game's moderation filter. Please try again."
            )

        game_state = get_game_state(context)
        game_state.tone = tone
        save_game_state(game_state, context)

    @post("/onboarding/game/genre")
    def set_game_genre(self, genre: str, context_id: Optional[str] = None, **kwargs):
        context = self.agent_service.build_default_context(
            context_id=context_id, **kwargs
        )

        if not _is_allowed_by_moderation(genre, context):
            raise SteamshipError(
                "Supplied 'genre' was rejected by game's moderation filter. Please try again."
            )

        game_state = get_game_state(context)
        game_state.genre = genre
        save_game_state(game_state, context)

    # TODO: add complete endpoint that retrieves game state from context and validates the inputs
    # have been properly assembled (as opposed to a full set below).

    @post("/complete_onboarding")
    def complete_onboarding(self, context_id: Optional[str] = None, **kwargs) -> bool:
        """Attempts to complete onboarding."""
        try:
            game_state = GameState.parse_obj(kwargs)
            context = self.agent_service.build_default_context(context_id=context_id)

            if game_state.active_mode != ActiveMode.ONBOARDING:
                raise SteamshipError(
                    message=f"Unable to complete onboarding -- it appears to be complete! Currently in state {game_state.active_mode.value}"
                )

            # TODO: streamline for mass validation ?
            self.set_character_name(game_state.player.name)
            self.set_character_background(game_state.player.background)
            self.set_character_description(game_state.player.description)
            self.set_character_motivation(game_state.player.motivation)
            self.set_game_genre(game_state.genre)
            self.set_game_tone(game_state.tone)

            game_state = get_game_state(context)

            # TODO: This should really be from the agent service
            function_capable_llm = ChatOpenAI(self.client)
            self.onboarding_agent = OnboardingAgent(
                client=self.client, tools=[], llm=function_capable_llm
            )

            self.onboarding_agent.run(context)
            return True
        except RunNextAgentException:
            return game_state.chat_history_for_onboarding_complete
        except BaseException as e:
            logging.exception(e)
            raise e

    @post("/generate_story_intro")
    def generate_story_intro(self) -> str:
        context = self.agent_service.build_default_context()
        game_state = get_game_state(context)
        story_intro = generate_story_intro(player=game_state.player, context=context)
        return story_intro
