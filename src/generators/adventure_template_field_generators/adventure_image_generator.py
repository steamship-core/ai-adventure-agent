from steamship import Block, PluginInstance
from steamship.agents.schema import AgentContext

from generators.adventure_template_field_generator import (
    AdventureTemplateFieldGenerator,
)
from generators.image_generators import get_image_generator
from utils.context_utils import get_server_settings, get_theme


class AdventureImageGenerator(AdventureTemplateFieldGenerator):
    @staticmethod
    def get_field() -> str:
        return "image"

    def inner_generate(
        self, variables: dict, generator: PluginInstance, context: AgentContext
    ) -> Block:
        server_settings = get_server_settings(context)
        theme = get_theme(server_settings.camp_image_theme, context)
        generator = get_image_generator(theme)
        task = generator.request_adventure_image_generation(context)
        task.wait()
        return task.output.blocks[0]
