from typing import Optional

from steamship.agents.schema import AgentContext

from generators.image_generator import ImageGenerator
from generators.image_generators import get_image_generator
from generators.music_generator import MusicGenerator
from generators.music_generators.meta_music_generator import MetaMusicGenerator
from generators.social_media.haiku_tweet_generator import HaikuTweetGenerator
from generators.social_media_generator import SocialMediaGenerator
from schema.server_settings import get_theme
from utils.context_utils import get_server_settings

_CAMP_IMAGE_GENERATOR_KEY = "camp-image-generator"
_ITEM_IMAGE_GENERATOR_KEY = "item-image-generator"
_PROFILE_IMAGE_GENERATOR_KEY = "profile-image-generator"
_MUSIC_GENERATOR_KEY = "music-generator"
_SOCIAL_MEDIA_GENERATOR_KEY = "social-media-generator"


def get_camp_image_generator(context: AgentContext) -> Optional[ImageGenerator]:
    generator = context.metadata.get(_CAMP_IMAGE_GENERATOR_KEY)
    if not generator:
        # Lazily create
        server_settings = get_server_settings(context)
        theme = get_theme(server_settings.camp_image_theme, context)
        generator = get_image_generator(theme)
        context.metadata[_CAMP_IMAGE_GENERATOR_KEY] = generator

    return generator


def get_item_image_generator(context: AgentContext) -> Optional[ImageGenerator]:
    generator = context.metadata.get(_ITEM_IMAGE_GENERATOR_KEY)
    if not generator:
        # Lazily create
        server_settings = get_server_settings(context)
        theme = get_theme(server_settings.item_image_theme, context)
        generator = get_image_generator(theme)
        context.metadata[_ITEM_IMAGE_GENERATOR_KEY] = generator

    return generator


def get_profile_image_generator(context: AgentContext) -> Optional[ImageGenerator]:
    generator = context.metadata.get(_PROFILE_IMAGE_GENERATOR_KEY)
    if not generator:
        # Lazily create
        server_settings = get_server_settings(context)
        theme = get_theme(server_settings.profile_image_theme, context)
        generator = get_image_generator(theme)
        context.metadata[_PROFILE_IMAGE_GENERATOR_KEY] = generator

    return generator


def get_music_generator(context: AgentContext) -> Optional[MusicGenerator]:
    generator = context.metadata.get(_MUSIC_GENERATOR_KEY)
    if not generator:
        # Lazily create
        generator = MetaMusicGenerator()
        context.metadata[_MUSIC_GENERATOR_KEY] = generator

    return generator


def get_social_media_generator(context: AgentContext) -> Optional[SocialMediaGenerator]:
    generator = context.metadata.get(_SOCIAL_MEDIA_GENERATOR_KEY)
    if not generator:
        # Lazily create
        generator = HaikuTweetGenerator()
        context.metadata[_SOCIAL_MEDIA_GENERATOR_KEY] = generator

    return generator


def set_camp_image_generator(context: AgentContext, generator: ImageGenerator):
    context.metadata[_CAMP_IMAGE_GENERATOR_KEY] = generator


def set_item_image_generator(context: AgentContext, generator: ImageGenerator):
    context.metadata[_ITEM_IMAGE_GENERATOR_KEY] = generator


def set_profile_image_generator(context: AgentContext, generator: ImageGenerator):
    context.metadata[_PROFILE_IMAGE_GENERATOR_KEY] = generator


def set_music_generator(context: AgentContext, generator: MusicGenerator):
    context.metadata[_MUSIC_GENERATOR_KEY] = generator
