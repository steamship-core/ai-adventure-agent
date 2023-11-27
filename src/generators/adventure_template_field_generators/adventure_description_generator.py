from steamship import Block, PluginInstance
from steamship.agents.schema import AgentContext

from generators.adventure_template_field_generator import (
    AdventureTemplateFieldGenerator,
)
from generators.utils import safe_format


class AdventureDescriptionGenerator(AdventureTemplateFieldGenerator):
    PROMPT = """I need help! I need to create the back of a book jacket for an amazing story. It should captivate people so that they want to read it!

It should only be one or two (short) paragraphs.

Title: {name}
Tagline: {short_description}

Suggested one-sentence description:"""

    @staticmethod
    def get_field() -> str:
        return "description"

    def inner_generate(
        self, variables: dict, generator: PluginInstance, context: AgentContext
    ) -> Block:
        task = generator.generate(
            text=safe_format(self.PROMPT, variables),
            streaming=True,
            append_output_to_file=True,
            make_output_public=True,
        )
        return self.task_to_str_block(task)
