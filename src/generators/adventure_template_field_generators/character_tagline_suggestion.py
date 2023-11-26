from steamship import Block, PluginInstance
from steamship.agents.schema import AgentContext

from generators.adventure_template_field_generator import (
    AdventureTemplateFieldGenerator,
)
from generators.utils import safe_format


class CharacterTaglineSuggestionGenerator(AdventureTemplateFieldGenerator):
    PROMPT = """Suggest short, 5-10 word tagline of Character #{this_index} in a story.

Examples of good taglines illustrate the character's main motivation or struggle, ike this:

- (Karate Girl) Knows the ropes. But does she know herself?
- (Lawyer Sue) Sue everyone.
- (Mr. Meatball) Become the biggest meatball.
- (Dragonmaster) Ascend to the throne

Story Name: {name}
Story Genre: {narrative_voice}
Story Goal: {adventure_goal}
Character ${this_index} tagline: (${this_name}) """

    @staticmethod
    def get_field() -> str:
        return "characters.tagline"

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
