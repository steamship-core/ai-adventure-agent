from steamship import Block, PluginInstance
from steamship.agents.schema import AgentContext

from generators.server_settings_field_generator import ServerSettingsFieldGenerator
from generators.utils import safe_format


class AdventureDescriptionGenerator(ServerSettingsFieldGenerator):
    PROMPT = """I need help! Please create a two paragraph pitch for an upcoming award-winning story.

It should be one or two (short) paragraphs, written very well, and not sound like advertising.

Title: {name}
Genre: {narrative_voice}
Writing Style: {narrative_tone}
One-liner: {short_description}

Two paragraph pitch:"""

    @staticmethod
    def get_field() -> str:
        return "description"

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
