from steamship import Block, PluginInstance
from steamship.agents.schema import AgentContext

from generators.editor_field_suggestion_generator import EditorFieldSuggestionGenerator
from generators.image_generators.stable_diffusion_with_loras import (
    StableDiffusionWithLorasImageGenerator,
)
from utils.context_utils import get_server_settings


class CharacterImageSuggestionGenerator(EditorFieldSuggestionGenerator):
    @staticmethod
    def get_field() -> str:
        return "characters.image"

    def suggest(
        self, variables: dict, generator: PluginInstance, context: AgentContext
    ) -> Block:
        image_generator = StableDiffusionWithLorasImageGenerator()
        server_settings = get_server_settings(context)

        task = image_generator.generate(
            context,
            theme_name=server_settings.profile_image_theme,
            prompt=server_settings.profile_image_prompt,
            negative_prompt=server_settings.profile_image_negative_prompt,
            template_vars=variables,
            image_size="portrait_4_3",
            tags=[],
        )
        task.wait()

        return task.output.blocks[0]
