from steamship import Block, PluginInstance
from steamship.agents.schema import AgentContext

from generators.adventure_template_field_generator import (
    AdventureTemplateFieldGenerator,
)
from generators.utils import safe_format


class CharacterTaglineGenerator(AdventureTemplateFieldGenerator):
    PROMPT_NO_BACKGROUND = """Suggest short, 5-10 word tagline of Character #{this_index} in a story.

Examples of good taglines illustrate the character's main motivation or struggle, like this:

- Karate Girl - Knows the ropes. But does she know herself?
- Lawyer Sue - Sue everyone.
- Mr. Meatball - Become the biggest meatball.
- Dragonmaster - Ascend to the throne

Story Name: {name}
Story Genre: {narrative_voice}
Story Goal: {adventure_goal}
Character ${this_index} tagline: (${this_name}) """

    PROMPT_BACKGROUND = """Write or propose the one-line description of Character #{this_index} in this story pitch.

{adventure_background}

Character #{this_index} Name: {this_name}
Character #{this_index} Summary (one or two sentences):"""

    @staticmethod
    def get_field() -> str:
        return "characters.tagline"

    def inner_generate(
        self, variables: dict, generator: PluginInstance, context: AgentContext
    ) -> Block:
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
                    "this_index": variables.get("this_index"),
                    "this_name": variables.get("this_name"),
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

        this_name = variables.get("this_name")
        block.text = block.text.lstrip(f"{this_name} - ")

        return block
