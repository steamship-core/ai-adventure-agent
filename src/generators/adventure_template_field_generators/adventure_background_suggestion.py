from steamship import Block, PluginInstance
from steamship.agents.schema import AgentContext

from generators.adventure_template_field_generator import (
    AdventureTemplateFieldGenerator,
)
from generators.utils import safe_format


class AdventureBackgroundSuggestionGenerator(AdventureTemplateFieldGenerator):
    PROMPT = """I need help! Write a few notes for a director about an scene in a short story.

Be colorful, descriptive, but concise! Use Markdown and bullet points. Include the sections: tone, narrative voice, adventure background story, non-protagonist characters, locations, and important items to the story.

## Genre

{narrative_voice}

## Writing Style

{narrative_tone}

-"""

    @staticmethod
    def get_field() -> str:
        return "adventure_background"

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
