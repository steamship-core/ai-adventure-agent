from steamship import Block, PluginInstance
from steamship.agents.schema import AgentContext

from generators.adventure_template_field_generator import (
    AdventureTemplateFieldGenerator,
)
from generators.utils import safe_format


class CharacterNameGenerator(AdventureTemplateFieldGenerator):
    PROMPT_NO_BACKGROUND = """Suggest the name of supporting character #{this_index} in a short story.

Story Title: {name}
Story Genre: {narrative_voice}, {narrative_tone}
Story Synopsis: {short_description}
Goal: {adventure_goal}{existing_chars}
Supporting Character #{this_index} Name:"""

    PROMPT_BACKGROUND = """What is the name of Character #{this_index} in this story pitch?

{adventure_background}

Character #{this_index} Name:"""

    @staticmethod
    def get_field() -> str:
        return "characters.name"

    def inner_generate(
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
                existing_char_names_str += f"\nCharacter #{_i} Name: {_ec}"

        adventure_background = variables.get("adventure_background")

        prompt = (
            self.PROMPT_BACKGROUND
            if (adventure_background and "haracters" in adventure_background)
            else self.PROMPT_NO_BACKGROUND
        )

        task = generator.generate(
            text=safe_format(
                prompt,
                {
                    "name": variables.get("name"),
                    "short_description": variables.get("short_description"),
                    "narrative_voice": variables.get("narrative_voice"),
                    "narrative_tone": variables.get("narrative_tone"),
                    "adventure_goal": variables.get("adventure_goal"),
                    "existing_chars": variables.get("existing_char_names_str"),
                    "this_index": variables.get("this_index", "0"),
                    "adventure_background": variables.get("adventure_background"),
                },
            ),
            streaming=True,
            append_output_to_file=True,
            make_output_public=True,
        )
        block = self.task_to_str_block(task)
        if ":" in block.text:
            # Handle the response of: 'Character 1 name: Foo'
            block.text = block.text.split(":")[1]
        return block
