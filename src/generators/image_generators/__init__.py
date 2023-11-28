from generators.image_generator import ImageGenerator
from generators.image_generators.dalle import DalleImageGenerator
from generators.image_generators.stable_diffusion_with_loras import (
    StableDiffusionWithLorasImageGenerator,
)
from schema.image_theme import ImageTheme


def get_image_generator(theme: ImageTheme) -> ImageGenerator:
    if theme.is_dalle:
        return DalleImageGenerator()
    return StableDiffusionWithLorasImageGenerator()
