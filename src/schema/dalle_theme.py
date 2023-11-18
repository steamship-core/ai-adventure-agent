from typing import Optional

from pydantic import BaseModel, Field

from generators.utils import safe_format


class DalleTheme(BaseModel):
    """A Theme for a DALL-E model.

    This class is meant to completely capture a coherent set of generation config.

    The one thing it DOESN'T include is the fragment of "user prompt" that is custom to any one generation.

    This allows someone to separate:
     - the prompt (e.g. "a chest of pirate gold") from
     - the theme (model, style, quality, etc.)

     NOTE: DALL-E themes DO NOT support negative prompts. Any negative prompts will be ignored (currently)!
    """

    name: str = Field(description="The name of this theme")

    model: str = Field(
        "dall-e-3",
        description="Model to use for image generation. Must be one of: ['dall-e-2', 'dall-e-3'].",
    )

    quality: str = Field(
        default="standard",
        description="The quality of the image that will be generated. Must be one of: ['hd', 'standard']."
        "'hd' creates images with finer details and greater consistency across the image. "
        "This param is only supported for the `dall-e-3` model.",
    )

    style: str = Field(
        default="vivid",
        description="The style of the generated images. Must be one of: ['vivid', 'natural']. "
        "Vivid causes the model to lean towards generating hyper-real and dramatic images. "
        "Natural causes the model to produce more natural, less hyper-real looking images. "
        "This param is only supported for `dall-e-3`.",
    )

    # TODO(dougreid): add validation for style and quality

    # TODO(dougreid): are the following necessary?
    prompt_prefix: Optional[str] = Field(
        description="Any extra words to include in your prompt. Include a comma and spacing if you require it."
    )

    prompt_suffix: Optional[str] = Field(
        description="Any extra words to always include in your prompt. Include a command and spacing if you require it."
    )

    def make_prompt(self, prompt: str, prompt_params: Optional[dict] = None):
        """Applies the included suffixes and then interpolates any {referenced} variables."""
        template = f"{self.prompt_prefix or ''}{prompt}{self.prompt_suffix or ''}"
        return safe_format(template, prompt_params or {})


DALL_E_3_VIVID_STANDARD = DalleTheme(
    name="dall_e_3_vivid_standard",
    model="dall-e-3",
    style="vivid",
    quality="standard",
)

DALL_E_3_VIVID_HD = DalleTheme(
    name="dall_e_3_vivid_hd",
    model="dall-e-3",
    style="vivid",
    quality="hd",
)

DALL_E_3_NATURAL_STANDARD = DalleTheme(
    name="dall_e_3_natural_standard",
    model="dall-e-3",
    style="natural",
    quality="standard",
)

DALL_E_3_NATURAL_HD = DalleTheme(
    name="dall_e_3_natural_hd",
    model="dall-e-3",
    style="natural",
    quality="hd",
)

# Premade themes that we know work well
PREMADE_THEMES = [
    DALL_E_3_NATURAL_HD,
    DALL_E_3_NATURAL_STANDARD,
    DALL_E_3_VIVID_HD,
    DALL_E_3_VIVID_STANDARD,
]

DEFAULT_THEME = DALL_E_3_VIVID_STANDARD
