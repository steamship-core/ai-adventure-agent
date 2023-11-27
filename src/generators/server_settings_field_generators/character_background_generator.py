from steamship import Block, PluginInstance
from steamship.agents.schema import AgentContext

from generators.server_settings_field_generator import ServerSettingsFieldGenerator
from generators.utils import safe_format


class CharacterBackgroundGenerator(ServerSettingsFieldGenerator):

    PROMPT = """Propose actor's notes for an award-winning character in a story.

Story Title: {name}
Story Genre: {narrative_voice}, {narrative_tone}
Story Synopsis: {short_description}
Character: {this_name}
Character Tagline: {this_tagline}
Character Goal: {adventure_goal}

Now, propose actor notes for {this_name}'s background.
Be colorful, but concise, and make sure to make everything very specific! Show, don't tell!
The proposed background should include origins, personal drive and failings, and a rich and exciting arc of progress toward the goal!
It should only be two or three short paragraphs.

Actor Notes for {this_name}'s Background:"""

    @staticmethod
    def get_field() -> str:
        return "characters.background"

    def inner_generate(
        self, variables: dict, generator: PluginInstance, context: AgentContext
    ) -> Block:
        task = generator.generate(
            text=safe_format(self.PROMPT, variables),
            streaming=True,
            append_output_to_file=True,
            make_output_public=True,
        )
        return self.task_to_str_block(task)
