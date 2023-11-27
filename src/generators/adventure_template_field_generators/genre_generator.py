from steamship import Block, PluginInstance
from steamship.agents.schema import AgentContext

from generators.adventure_template_field_generator import (
    AdventureTemplateFieldGenerator,
)
from generators.utils import safe_format


class GenreGenerator(AdventureTemplateFieldGenerator):
    PROMPT = """Suggest a genre for a short story. Be creative, expansive, but concise!

Examples of genres:

- fantasy adventure
- children’s book
- young adult novel
- fanfic
- high literature

Genre Suggestion:"""

    @staticmethod
    def get_field() -> str:
        return "narrative_voice"

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
