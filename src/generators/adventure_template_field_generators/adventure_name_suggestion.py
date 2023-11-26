import random

from steamship import Block, PluginInstance
from steamship.agents.schema import AgentContext

from generators.adventure_template_field_generator import (
    AdventureTemplateFieldGenerator,
)
from generators.utils import safe_format


class AdventureNameSuggestionGenerator(AdventureTemplateFieldGenerator):
    PROMPT = """I need help! Create an amazing movie title for a {genre} movie people would want to see.

Make it short: only a few words. Make it punchy!

Suggested Title:"""

    @staticmethod
    def get_field() -> str:
        return "name"

    def suggest(
        self, variables: dict, generator: PluginInstance, context: AgentContext
    ) -> Block:

        genre = variables.get("narrative_voice")
        if not genre:
            genre = random.choice(
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
            text=safe_format(self.PROMPT, {"genre": genre}),
            streaming=True,
            append_output_to_file=True,
            make_output_public=True,
        )
        return self.task_to_str_block(task)
