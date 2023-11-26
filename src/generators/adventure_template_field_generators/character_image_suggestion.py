from steamship import Block, PluginInstance
from steamship.agents.schema import AgentContext

from generators.adventure_template_field_generator import (
    AdventureTemplateFieldGenerator,
)
from generators.generator_context_utils import get_profile_image_generator


class CharacterImageSuggestionGenerator(AdventureTemplateFieldGenerator):
    @staticmethod
    def get_field() -> str:
        return "characters.image"

    def suggest(
        self, variables: dict, generator: PluginInstance, context: AgentContext
    ) -> Block:
        generator = get_profile_image_generator(context)
        task = generator.request_profile_image_generation(context)
        task.wait()
        return task.output.blocks[0]
