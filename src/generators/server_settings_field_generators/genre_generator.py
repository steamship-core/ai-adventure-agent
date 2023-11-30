from random import shuffle
from typing import Optional

from steamship import Block, MimeTypes, PluginInstance
from steamship.agents.schema import AgentContext

from generators.server_settings_field_generator import ServerSettingsFieldGenerator
from generators.utils import safe_format

EXAMPLE_GENRES = [
    "fantasy adventure",
    "children's book",
    "romance",
    "science fiction",
    "parody television show",
    "political thriller",
    "speculative fiction",
    "historical fiction",
    "cyberpunk",
    "steampunk",
    "fantasy adventure",
    "round the world adventure",
    "bedtime story",
    "philosophical quandry",
    "horror",
    "mystery",
    "comedy",
    "adventure",
    "fantasy",
    "sci-fi",
    "young adult",
    "coming of age",
    "who dunnit",
    "pirate adventure",
    "animal story",
    "buddy cop story",
    "coming of age",
    "police mystery",
    "thriller",
    "kids adventure",
    "tragedy",
    "romantic comedy",
    "romance",
    "video games",
    "dungeon's and dragons",
]


class GenreGenerator(ServerSettingsFieldGenerator):
    PROMPT = """Suggest a genre for a short story. Be creative, but concise!

Examples of genres:

{genre_examples}

Genre Suggestion:"""

    PROMPT_FROM_DESCRIPTION = """# Goal

Tell me the genre for this upcoming award-winning piece of writing.

Examples of genres:

{genre_examples}

# Description of story

{description}

# Genre (and only the genre -- no other text!): """

    @staticmethod
    def get_field() -> str:
        return "narrative_voice"

    def inner_generate(
        self,
        variables: dict,
        generator: PluginInstance,
        context: AgentContext,
        generation_config: Optional[dict] = None,
    ) -> Block:

        shuffle(EXAMPLE_GENRES)

        if (
            generation_config
            and generation_config.get("variant") == "generate-from-description"
        ):
            selected = EXAMPLE_GENRES[:1]
            genre_examples = "\n".join([f"- {genre}" for genre in selected])
            variables["genre_examples"] = genre_examples
            prompt = self.PROMPT_FROM_DESCRIPTION
            task = generator.generate(
                text=safe_format(prompt, variables),
                streaming=True,
                append_output_to_file=True,
                make_output_public=True,
            )
            return self.task_to_str_block(task)
        else:
            return Block(text=EXAMPLE_GENRES[0], mime_type=MimeTypes.TXT)
