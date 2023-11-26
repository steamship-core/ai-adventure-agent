import random

from steamship import Block, PluginInstance
from steamship.agents.schema import AgentContext

from generators.editor_field_suggestion_generator import EditorFieldSuggestionGenerator
from generators.utils import safe_format


class AdventureNameSuggestionGenerator(EditorFieldSuggestionGenerator):
    PROMPT = """I need help! I need to create an amazing movie title for an interesting movie.

I want it to be about five words -- no longer.

The genre is {genre} and it's got a {genre} vibe!

Suggested Title:"""

    @staticmethod
    def get_field() -> str:
        return "name"

    def suggest(
        self, variables: dict, generator: PluginInstance, context: AgentContext
    ) -> Block:
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

        vibe = random.choice(
            [
                "silly",
                "serious",
                "punchy",
                "pixar-like",
                "novel-like",
                "heady",
                "fast paced",
                "irreverant",
                "parody",
                "gonzo",
                "touching",
                "fun",
                "exciting",
                "creative",
                "speculative",
                "whimsical",
            ]
        )
        task = generator.generate(
            text=safe_format(self.PROMPT, {"genre": genre, "vibe": vibe}),
            streaming=True,
            append_output_to_file=True,
            make_output_public=True,
        )
        return self.task_to_str_block(task)
