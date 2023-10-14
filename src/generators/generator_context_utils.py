from typing import Optional

from steamship.agents.schema import AgentContext

from generators.image_generator import ImageGenerator
from generators.image_generators.stable_diffusion_with_loras import (
    StableDiffusionWithLorasImageGenerator,
)

_IMAGE_GENERATOR_KEY = "image-generator"


def get_image_generator(context: AgentContext) -> Optional[ImageGenerator]:
    generator = context.metadata.get(_IMAGE_GENERATOR_KEY)
    if not generator:
        # Lazily create
        generator = StableDiffusionWithLorasImageGenerator()
        context.metadata[_IMAGE_GENERATOR_KEY] = generator

    return generator
