from typing import Optional

from steamship import Block, PluginInstance
from steamship.agents.schema import AgentContext

from generators.server_settings_field_generator import ServerSettingsFieldGenerator
from generators.utils import safe_format


class CharacterDescriptionGenerator(ServerSettingsFieldGenerator):
    PROMPT = """I need help making the artwork for a character in a story. Here is the context:

Story Title: {name}
Story Genre: {narrative_voice}, {narrative_tone}
Character Name: {this_name}
Character Tagline: {this_tagline}
Character Background: {this_background}

Now help me write a concise, colorful, and very specific physical description for this character. Don't use the character's name; just provide the description.

Character Physical Description (one line):"""

    @staticmethod
    def get_field() -> str:
        return "characters.description"

    def inner_generate(
        self,
        variables: dict,
        generator: PluginInstance,
        context: AgentContext,
        generation_config: Optional[dict] = None,
    ) -> Block:
        task = generator.generate(
            text=safe_format(
                self.PROMPT,
                {
                    "name": variables.get("name"),
                    "short_description": variables.get("short_description"),
                    "narrative_voice": variables.get("narrative_voice"),
                    "narrative_tone": variables.get("narrative_tone"),
                    "this_name": variables.get("this_name"),
                    "this_tagline": variables.get("this_tagline"),
                    "this_background": variables.get("this_background"),
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
