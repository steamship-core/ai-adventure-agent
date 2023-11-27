from steamship import Block, PluginInstance
from steamship.agents.schema import AgentContext

from generators.adventure_template_field_generator import (
    AdventureTemplateFieldGenerator,
)
from generators.utils import safe_format


class NarrativeToneGenerator(AdventureTemplateFieldGenerator):
    PROMPT = """Write a narrative tone suggestion for a story with the genre {narrative_voice}. Be creative! Wide-ranging! But keep it concise.

Examples of good outputs:

- silly, like a Cartoon Network show
- parody, in the style of an HBO show
- dramatic, with a tinge of danger
- gritty, high contrast and real
- film noir, with a romantic tinge of hard-boiled mystery

Suggestion:

-"""

    @staticmethod
    def get_field() -> str:
        return "narrative_tone"

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
