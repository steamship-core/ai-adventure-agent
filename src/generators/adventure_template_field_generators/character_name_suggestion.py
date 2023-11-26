from steamship import Block, PluginInstance
from steamship.agents.schema import AgentContext

from generators.editor_field_suggestion_generator import EditorFieldSuggestionGenerator
from generators.utils import safe_format


class CharacterNameSuggestionGenerator(EditorFieldSuggestionGenerator):
    PROMPT = """Suggest the name of supporting character #{this_index} in a short story.

Story Title: {name}
Story Genre: {narrative_voice}
Protagonist: {adventure_goal}{existing_chars}
Supporting Character #{this_index} Name:"""

    @staticmethod
    def get_field() -> str:
        return "characters.name"

    def suggest(
        self, variables: dict, generator: PluginInstance, context: AgentContext
    ) -> Block:
        existing_char_names_str = ""
        existing_char_names = []
        if chars := variables.get("characters"):
            for char in chars:
                if char is None:
                    continue
                if _name := char.get("name"):
                    existing_char_names.append(_name)
        if existing_char_names:
            for _i, _ec in enumerate(existing_char_names):
                existing_char_names_str += f"\nSupporting Character #{_i} Name: {_ec}"

        task = generator.generate(
            text=safe_format(
                self.PROMPT,
                {
                    "name": variables.get("name"),
                    "narrative_voice": variables.get("narrative_voice"),
                    "adventure_goal": variables.get("adventure_goal"),
                    "existing_chars": variables.get("existing_char_names_str"),
                    "this_index": variables.get("this_index"),
                },
            ),
            streaming=True,
            append_output_to_file=True,
            make_output_public=True,
        )
        return self.task_to_str_block(task)
