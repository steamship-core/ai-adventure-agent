from typing import Optional

from steamship.agents.schema import AgentContext

from generators.image_generator import ImageGenerator
from generators.image_generators.stable_diffusion_with_loras import (
    StableDiffusionWithLorasImageGenerator,
)
from generators.music_generator import MusicGenerator
from generators.music_generators.meta_music_generator import MetaMusicGenerator
from generators.social_media.haiku_tweet_generator import HaikuTweetGenerator
from generators.social_media_generator import SocialMediaGenerator

_IMAGE_GENERATOR_KEY = "image-generator"
_MUSIC_GENERATOR_KEY = "music-generator"
_SOCIAL_MEDIA_GENERATOR_KEY = "social-media-generator"


def get_image_generator(context: AgentContext) -> Optional[ImageGenerator]:
    generator = context.metadata.get(_IMAGE_GENERATOR_KEY)
    if not generator:
        # Lazily create
        generator = StableDiffusionWithLorasImageGenerator()
        context.metadata[_IMAGE_GENERATOR_KEY] = generator

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
