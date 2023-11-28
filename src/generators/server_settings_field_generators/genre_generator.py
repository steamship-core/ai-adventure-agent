from typing import Optional

from steamship import Block, PluginInstance
from steamship.agents.schema import AgentContext

from generators.server_settings_field_generator import ServerSettingsFieldGenerator
from generators.utils import safe_format


class GenreGenerator(ServerSettingsFieldGenerator):
    PROMPT = """Suggest a genre for a short story. Be creative, expansive, but concise!

Examples of genres:

- fantasy adventure
- children’s book
- young adult novel
- fanfic
- high literature

Genre Suggestion:"""

    PROMPT_FROM_DESCRIPTION = """# Goal

Tell me the genre for this upcoming award-winning piece of writing.

Examples of genres:

- fantasy adventure
- children’s book
- young adult novel
- fanfic
- high literature

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
        if (
            generation_config
            and generation_config.get("variant") == "generate-from-description"
        ):
            prompt = self.PROMPT_FROM_DESCRIPTION
        else:
            prompt = self.PROMPT

        task = generator.generate(
            text=safe_format(prompt, variables),
            streaming=True,
            append_output_to_file=True,
            make_output_public=True,
        )
        return self.task_to_str_block(task)
