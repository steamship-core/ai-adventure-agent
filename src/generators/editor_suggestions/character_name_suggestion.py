from steamship import Block, PluginInstance
from steamship.agents.schema import AgentContext

from generators.editor_field_suggestion_generator import EditorFieldSuggestionGenerator
from generators.utils import safe_format


class CharacterNameSuggestionGenerator(EditorFieldSuggestionGenerator):
    PROMPT = """Suggest the name of Character #{this_index} in a story.

Story Name: {name}
Story Genre: {narrative_voice}
Story Goal: {adventure_goal}
Character ${this_index} name:"""

    @staticmethod
    def get_field() -> str:
        return "characters.name"

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
