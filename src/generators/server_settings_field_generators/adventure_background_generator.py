from steamship import Block, PluginInstance
from steamship.agents.schema import AgentContext

from generators.server_settings_field_generator import ServerSettingsFieldGenerator
from generators.utils import safe_format


class AdventureBackgroundGenerator(ServerSettingsFieldGenerator):
    PROMPT = """We need help! Hell fill out this story pitch for a director who needs to develop it into an award winning story.

Be colorful, descriptive, but concise! Use Markdown, level-two headers, and bullet points within them.

Include the sections: Title, Writing Style, Plot Pitch, Main Goal, Colorful World Setting, Three Characters, Four Locations, and Important Plot Points.

## Title

{name}
{short_description}

## Writing Style

* {narrative_voice}
* {narrative_tone}

## Plot Pitch

{description}

## Main Goal

{adventure_goal}

##"""

    @staticmethod
    def get_field() -> str:
        return "adventure_background"

    def inner_generate(
        self, variables: dict, generator: PluginInstance, context: AgentContext
    ) -> Block:
        task = generator.generate(
            text=safe_format(self.PROMPT, variables),
            streaming=True,
            append_output_to_file=True,
            make_output_public=True,
        )
        block = self.task_to_str_block(task)
        block.text = f"## {block.text}"
        return block
