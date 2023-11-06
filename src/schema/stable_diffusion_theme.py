from typing import List, Optional

from pydantic import BaseModel, Field

from generators.utils import safe_format


class StableDiffusionTheme(BaseModel):
    """A Theme for a Stable diffusion model.

    This class is meant to completely capture a coherent set of generation config: model, loras, lora activations, etc.

    The one thing it DOESN'T include is the fragment of "user prompt" that is custom to any one generation.

    This allows someone to separate:
     - the prompt (e.g. "a chest of pirate gold") from
     - the theme (SDXL w/ Lora 1, 2, a particula negative prompt addition, etc.
    """

    name: str = Field(description="The name of this theme")

    prompt_prefix: Optional[str] = Field(
        description="Any extra words, including trigger words for LoRAs in this theme. Include a comma and spacing if you require it."
    )

    prompt_suffix: Optional[str] = Field(
        description="Any extra words, including trigger words for LoRAs in this theme. Include a command and spacing if you require it."
    )

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

    guidance_scale: int = Field(
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

    def make_prompt(self, prompt: str, prompt_params: Optional[dict] = None):
        """Applies the included suffixes and then interpolates any {referenced} variables."""
        template = f"{self.prompt_prefix or ''}{prompt}{self.prompt_suffix or ''}"
        return safe_format(template, prompt_params or {})

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

# https://civitai.com/models/120853/crayon-style-sdxl-and-sd15
# Note: This isn't included in the list below because we haven't gotten it to work well yet.
CRAYON = StableDiffusionTheme(
    name="crayon",
    guidance_scale=10,
    scheduler="DPM++ 2M Karras",
    steps=30,
    seed=1397624082,
    loras=["https://civitai.com/api/download/models/131462"],
)

# LZ-comics (https://civitai.com/models/164614/lz-comics) by https://civitai.com/user/Lunzi
# Note: This isn't included in the list below because we haven't gotten it to work well yet.
BW_COMIC_1 = StableDiffusionTheme(
    name="bw_comic_1",
    model="runwayml/stable-diffusion-v1-5",
    prompt_prefix="line art, comic, comic, koma, text bubble, monochrome, ",
    negative_prompt_prefix="(deformed, distorted, disfigured:1.3), poorly drawn, bad anatomy, wrong anatomy, extra limb, missing limb, floating limbs, (mutated hands and fingers:1.4), disconnected limbs, mutation, mutated, ugly, disgusting, blurry, amputation. tattoo, watermark, ",
    model_architecture="sd",
    loras=["https://civitai.com/api/download/models/185379"],
)


# One Piece (Wano Saga) Style LoRA
# (https://civitai.com/models/4219/one-piece-wano-saga-style-lora) by https://civitai.com/user/Lykon
# Note: This isn't included in the list below because we haven't gotten it to work well yet.
ONE_PIECE = StableDiffusionTheme(
    name="one-piece",
    model="runwayml/stable-diffusion-v1-5",
    prompt_prefix="((wanostyle)) ",
    negative_prompt_prefix="(deformed, distorted, disfigured:1.3), poorly drawn, bad anatomy, wrong anatomy, extra limb, missing limb, floating limbs, (mutated hands and fingers:1.4), disconnected limbs, mutation, mutated, ugly, disgusting, blurry, amputation. tattoo, watermark, ",
    model_architecture="sd",
    scheduler="Euler A",
    loras=["https://civitai.com/api/download/models/6331"],
)

# Premade themes that we know work well
PREMADE_THEMES = [PIXEL_ART_THEME_1, PIXEL_ART_THEME_2]

DEFAULT_THEME = PIXEL_ART_THEME_2
