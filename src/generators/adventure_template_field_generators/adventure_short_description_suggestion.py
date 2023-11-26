from steamship import Block, PluginInstance
from steamship.agents.schema import AgentContext

from generators.adventure_template_field_generator import (
    AdventureTemplateFieldGenerator,
)
from generators.utils import safe_format


class AdventureShortDescriptionSuggestionGenerator(AdventureTemplateFieldGenerator):
    PROMPT = """I need help! I need to create an amazing one-sentence tagline for a movie. It should captivate people so that they want to see it.

The title is: {name}

Suggested one-sentence description:"""

    @staticmethod
    def get_field() -> str:
        return "short_description"

    def suggest(
        self, variables: dict, generator: PluginInstance, context: AgentContext
    ) -> Block:

        task = generator.generate(
            text=safe_format(self.PROMPT, variables),
            streaming=True,
            append_output_to_file=True,
            make_output_public=True,
        )
        return self.task_to_str_block(task)
