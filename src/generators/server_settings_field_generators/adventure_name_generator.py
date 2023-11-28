import random

from steamship import Block, PluginInstance
from steamship.agents.schema import AgentContext

from generators.server_settings_field_generator import ServerSettingsFieldGenerator
from generators.utils import safe_format


class AdventureNameGenerator(ServerSettingsFieldGenerator):
    PROMPT = """I need help! Create an amazing movie title that people would want to see. Make it short: only a few words. Make it punchy!

Genre: {narrative_voice}
Writing Style: {narrative_tone}
Suggested Title:"""

    @staticmethod
    def get_field() -> str:
        return "name"

    def inner_generate(
        self, variables: dict, generator: PluginInstance, context: AgentContext
    ) -> Block:

        narrative_voice = variables.get("narrative_voice")
        narrative_tone = variables.get(
            "narrative_tone", "written in a fast-paced and enjoyable style"
        )

        if not narrative_voice:
            narrative_voice = random.choice(
                [
                    "comedy",
                    "adventure",
                    "fantasy",
                    "sci-fi",
                    "young adult",
                    "coming of age",
                    "who dunnit",
                    "murder mystery",
                    "thriller",
                    "kids adventure",
                    "tragedy",
                    "romantic comedy",
                    "romance",
                    "video games",
                    "dungeon's and dragons",
                ]
            )

        task = generator.generate(
            text=safe_format(
                self.PROMPT,
                {"narrative_voice": narrative_voice, "narrative_tone": narrative_tone},
            ),
            streaming=True,
            append_output_to_file=True,
            make_output_public=True,
        )
        return self.task_to_str_block(task)
