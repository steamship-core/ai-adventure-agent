from steamship import Block, PluginInstance
from steamship.agents.schema import AgentContext

from generators.editor_field_suggestion_generator import EditorFieldSuggestionGenerator
from generators.utils import safe_format


class AdventureTagSuggestionGenerator(EditorFieldSuggestionGenerator):
    SOME_TAGS = """Please create an additional categorization tag for this short story.

Examples of good tags are: Comedy, Thriller, Mystery, Silly, Family, Adventure, Sci-Fi, Romance.

The story title is: {name}
The story description is: {short_description}
The story genre is: {narrative_voice}
Existing tags are: {existing}
Additional categorization tag:"""

    PROMPT = """Please a single categorization tag for this short story.

Examples of good tags are: Comedy, Thriller, Mystery, Silly, Family, Adventure, Sci-Fi, Romance.

The story title is: {name}
The story description is: {short_description}
The story genre is: {narrative_voice}
Categorization tag:"""

    @staticmethod
    def get_field() -> str:
        return "tags"

    def suggest(
        self, variables: dict, generator: PluginInstance, context: AgentContext
    ) -> Block:
        if variables.get("tags"):
            prompt = self.SOME_TAGS
        else:
            prompt = self.PROMPT

        task = generator.generate(
            text=safe_format(
                prompt,
                {
                    "name": variables.get("name"),
                    "short_description": variables.get("short_description"),
                    "narrative_voice": variables.get("narrative_voice"),
                    "tags": variables.get("tags"),
                },
            ),
            streaming=True,
            append_output_to_file=True,
            make_output_public=True,
        )
        return self.task_to_str_block(task)
