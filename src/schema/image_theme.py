from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from generators.utils import safe_format


class ImageTheme(BaseModel):
    """Base model for image generation themes."""

    model_config = ConfigDict(
        # Allow extra fields (e.g. for use with base classes)
        extra="allow"
    )

    name: str = Field(description="The name of this theme")

    prompt_prefix: Optional[str] = Field(
        description="Any extra words, including trigger words for LoRAs in this theme. Include a comma and spacing if you require it."
    )

    prompt_suffix: Optional[str] = Field(
        description="Any extra words, including trigger words for LoRAs in this theme. Include a command and spacing if you require it."
    )

    model: str = Field(
        "stabilityai/stable-diffusion-xl-base-1.0",
        description='Either (1) dall-e-3 or dall-e-2, or (2) URL or HuggingFace ID of the base model to generate the image. Examples: "stabilityai/stable-diffusion-xl-base-1.0", "runwayml/stable-diffusion-v1-5", "SG161222/Realistic_Vision_V2.0". ',
    )

    def make_prompt(self, prompt: str, prompt_params: Optional[dict] = None):
        """Applies the included suffixes and then interpolates any {referenced} variables."""
        template = f"{self.prompt_prefix or ''}{prompt}{self.prompt_suffix or ''}"
        return safe_format(template, prompt_params or {})

    @property
    def is_dalle(self):
        return self.model in ["dall-e-2", "dall-e-3"]


class DalleTheme(ImageTheme):
    """A Theme for a DALL-E model.

    This class is meant to completely capture a coherent set of generation config.

    The one thing it DOESN'T include is the fragment of "user prompt" that is custom to any one generation.

    This allows someone to separate:
     - the prompt (e.g. "a chest of pirate gold") from
     - the theme (model, style, quality, etc.)

     NOTE: DALL-E themes DO NOT support negative prompts. Any negative prompts will be ignored (currently)!
    """

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


class StableDiffusionTheme(ImageTheme):
    """A Theme for a StableDiffusion model.

    This class is meant to completely capture a coherent set of generation config.

    This allows someone to separate:
     - the prompt (e.g. "a chest of pirate gold") from
     - the theme (model, style, quality, etc.)

    The one thing it DOESN'T include is the fragment of "user prompt" that is custom to any one generation.

    This allows someone to separate:
     - the prompt (e.g. "a chest of pirate gold") from
     - the theme (SDXL w/ Lora 1, 2, a particula negative prompt addition, etc.
    """

    negative_prompt_prefix: Optional[str] = Field(
        description="Any extra words, including trigger words for LoRAs in this theme. Include a comma and spacing if you require it."
    )

    negative_prompt_suffix: Optional[str] = Field(
        description="Any extra words, including trigger words for LoRAs in this theme. Include a command and spacing if you require it."
    )

    model: str = Field(
        "stabilityai/stable-diffusion-xl-base-1.0",
        description='URL or HuggingFace ID of the base model to generate the image. Examples: "stabilityai/stable-diffusion-xl-base-1.0", "runwayml/stable-diffusion-v1-5", "SG161222/Realistic_Vision_V2.0". ',
    )

    loras: List[str] = Field(
        [],
        description='The LoRAs to use for image generation. You can use any number of LoRAs and they will be merged together to generate the final image. MUST be specified as a json-serialized list that includes objects with the following params: - \'path\' (required)  - \'scale\' (optional, defaults to 1). Example: \'[{"path": "https://civitai.com/api/download/models/135931", "scale": 1}]',
    )

    seed: int = Field(
        -1,
        description="The same seed and prompt passed to the same version of StableDiffusion will output the same image every time.",
    )

    image_size: str = Field(
        "square_hd",
        description="The size of the generated image(s). You can choose between some presets or select custom height and width. Custom height and width values MUST be multiples of 8.Presets: ['square_hd', 'square', 'portrait_4_3', 'portrait_16_9', 'landscape_4_3', 'landscape_16_9'] Custom Example: '{\"height\": 512,\"width\": 2048}'",
    )

    num_inference_steps: int = Field(
        30,
        description="Increasing the number of steps tells Stable Diffusion that it should take more steps to generate your final result which can increase the amount of detail in your image.",
    )

    guidance_scale: float = Field(
        7.5,
        description="The CFG(Classifier Free Guidance) scale is a measure of how close you want the model to stick to your prompt when looking for a related image to show you.",
    )

    clip_skip: int = Field(
        0,
        description="Skips part of the image generation process, leading to slightly different results. This means the image renders faster, too.",
    )

    model_architecture: str = Field(
        "sdxl",
        description="The architecture of the model to use. If a HF model is used, it will be automatically detected. Supported: ['sd', 'sdxl']",
    )

    scheduler: str = Field(
        "DPM++ 2M",
        description="Scheduler (or sampler) to use for the image denoising process. Possible values: ['DPM++ 2M', 'DPM++ 2M Karras', 'DPM++ 2M SDE', 'DPM++ 2M SDE Karras', 'Euler', 'Euler A']",
    )

    image_format: str = Field(
        "png",
        description="The format of the generated image. Possible values: ['jpeg', 'png']",
    )

    def make_negative_prompt(
        self, negative_prompt: str, prompt_params: Optional[dict] = None
    ):
        """Applies the included suffixes and then interpolates any {referenced} variables."""
        template = f"{self.negative_prompt_prefix or ''}{negative_prompt}{self.negative_prompt_suffix or ''}"
        return safe_format(template, prompt_params or {})


# Pixel Art XL (https://civitai.com/models/120096/pixel-art-xl) by https://civitai.com/user/NeriJS
PIXEL_ART_THEME_1 = StableDiffusionTheme(
    name="pixel_art_1",
    prompt_prefix="(pixel art) ",
    loras=["https://civitai.com/api/download/models/135931"],
)

# Pixel Art SDXL RW (https://civitai.com/models/114334/pixel-art-sdxl-rw) by https://civitai.com/user/leonnn1
PIXEL_ART_THEME_2 = StableDiffusionTheme(
    name="pixel_art_2",
    prompt_prefix="((pixelart)) ",
    loras=["https://civitai.com/api/download/models/123593"],
)

# From https://www.fal.ai/models/sd-loras
PIXEL_ART_THEME_3 = StableDiffusionTheme(
    name="pixel_art_3",
    prompt_prefix="isometric, ",
    negative_prompt_prefix="cartoon, painting, illustration, (worst quality, low quality, normal quality:2), (watermark), immature, child, ",
    model_architecture="sdxl",
    num_inference_steps=50,
    guidance_scale=7.5,
    clip_skip=0,
    loras=["https://civitai.com/api/download/models/130580"],
)

# From https://www.fal.ai/models/sd-loras
CINEMATIC_ANIMATION = StableDiffusionTheme(
    name="cinematic_animation",
    model="https://civitai.com/api/download/models/46846",
    prompt_prefix="(masterpiece), (best quality), (incredible digital artwork), atmospheric scene inspired by a Peter Jackson fantasy movie, ",
    prompt_suffix=", awe-inspiring structures, diverse and vibrant characters, engaging in a pivotal moment, dramatic lighting, vivid colors, intricate details, expertly capturing the essence of an epic cinematic experience <lora:epiNoiseoffset_v2Pynoise:1>",
    negative_prompt_prefix="(worst quality:1.2), (low quality:1.2), (lowres:1.1), (monochrome:1.1), (greyscale), multiple views, comic, sketch, (((bad anatomy))), (((deformed))), (((disfigured))), watermark, multiple_views, mutation hands, mutation fingers, extra fingers, missing fingers, watermark, ",
    model_architecture="sd",
    num_inference_steps=90,
    guidance_scale=8,
    clip_skip=2,
)

# From https://www.fal.ai/models/sd-loras
FF7R = StableDiffusionTheme(
    name="ff7r",
    model="https://civitai.com/api/download/models/95489",
    prompt_prefix="ff7r style, blurry background, realistic, ",
    prompt_suffix=", ((masterpiece)) <lora:ff7r_style_ned_offset:1>",
    negative_prompt_prefix="nsfw, (worst quality, low quality:1.3), (depth of field, blurry:1.2), (greyscale, monochrome:1.1), 3D face, nose, cropped, lowres, text, jpeg artifacts, signature, watermark, username, blurry, artist name, trademark, watermark, title, (tan, muscular, loli, petite, child, infant, toddlers, chibi, sd character:1.1), multiple view, Reference sheet,",
    model_architecture="sd",
    num_inference_steps=80,
    guidance_scale=9,
    clip_skip=2,
    loras=["https://civitai.com/api/download/models/60948"],
)

# From https://www.fal.ai/models/sd-loras
EPIC_REALISM = StableDiffusionTheme(
    name="epic_realism",
    model="emilianJR/epiCRealism",
    prompt_prefix="photo, ",
    negative_prompt_prefix="cartoon, painting, illustration, (worst quality, low quality, normal quality:2)",
    model_architecture="sd",
    num_inference_steps=80,
    guidance_scale=5,
    clip_skip=0,
)

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
    PIXEL_ART_THEME_1,
    PIXEL_ART_THEME_2,
    PIXEL_ART_THEME_3,
    FF7R,
    CINEMATIC_ANIMATION,
    EPIC_REALISM,
    DALL_E_3_NATURAL_HD,
    DALL_E_3_NATURAL_STANDARD,
    DALL_E_3_VIVID_HD,
    DALL_E_3_VIVID_STANDARD,
]

DEFAULT_THEME = PIXEL_ART_THEME_2
