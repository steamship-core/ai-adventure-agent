from typing import Optional

from steamship import Block, PluginInstance
from steamship.agents.schema import AgentContext

from generators.server_settings_field_generator import ServerSettingsFieldGenerator
from generators.utils import safe_format


class WritingStyleGenerator(ServerSettingsFieldGenerator):
    PROMPT = """What is a genre and writing style for upcoming award-winning piece of writing? Be creative! Wide-ranging! But keep it concise.

Examples of good outputs:

- silly, written in the style of a Cartoon Network show with lots of absurd jokes
- parody, written in the style of an HBO show that mimics reality but with a sardonic twist
- folksy-horror, written in the voice of a Steven King thriller with colorful descriptions
- gritty, written with William Gibson-style lyricism and filled with the juxtaposition of technology and decay
- film noir, written in a slightly old fashioned, romantic voice with a dose of hard-boiled mystery

Suggested genre and writing style:

- {narrative_voice}, """

    PROMPT_FROM_DESCRIPTION = """# Goal

Write the genre and writing style for upcoming award-winning piece of writing? Be creative! Wide-ranging! But keep it concise.

Examples of good outputs:

- silly, written in the style of a Cartoon Network show with lots of absurd jokes
- parody, written in the style of an HBO show that mimics reality but with a sardonic twist
- folksy-horror, written in the voice of a Steven King thriller with colorful descriptions
- gritty, written with William Gibson-style lyricism and filled with the juxtaposition of technology and decay
- film noir, written in a slightly old fashioned, romantic voice with a dose of hard-boiled mystery

# Description of story

{description}

# Genre and writing style

{narrative_voice}, """

    @staticmethod
    def get_field() -> str:
        return "narrative_tone"

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
