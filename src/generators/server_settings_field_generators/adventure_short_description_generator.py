from typing import Optional

from steamship import Block, PluginInstance
from steamship.agents.schema import AgentContext

from generators.server_settings_field_generator import ServerSettingsFieldGenerator
from generators.utils import safe_format


class AdventureShortDescriptionGenerator(ServerSettingsFieldGenerator):
    PROMPT = """I need help! I create an amazing one-sentence pitch for a new story.

Write well, capturing the essence of the a main character's background, location, and goal.

Title: {name}
Genre: {narrative_voice}
Writing Style: {narrative_tone}
One-sentence Pitch:"""

    @staticmethod
    def get_field() -> str:
        return "short_description"

    def inner_generate(
        self,
        variables: dict,
        generator: PluginInstance,
        context: AgentContext,
        generation_config: Optional[dict] = None,
    ) -> Block:

        narrative_voice = variables.get("narrative_voice")
        narrative_tone = variables.get(
            "narrative_tone", "written in a fast-paced and enjoyable style"
        )
        name = variables.get("name", "Untitled")

        task = generator.generate(
            text=safe_format(
                self.PROMPT,
                {
                    "narrative_voice": narrative_voice,
                    "narrative_tone": narrative_tone,
                    "name": name,
                },
            ),
            streaming=True,
            append_output_to_file=True,
            make_output_public=True,
        )
        return self.task_to_str_block(task)
