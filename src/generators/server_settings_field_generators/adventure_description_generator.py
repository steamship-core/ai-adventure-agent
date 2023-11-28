from typing import Optional

from steamship import Block, PluginInstance
from steamship.agents.schema import AgentContext

from generators.server_settings_field_generator import ServerSettingsFieldGenerator
from generators.utils import safe_format


class AdventureDescriptionGenerator(ServerSettingsFieldGenerator):
    PROMPT_NO_SOURCE_STORY = """I need help! Please create a two paragraph pitch for an upcoming award-winning story.

It should be one or two (short) paragraphs, written very well, and not sound like advertising.

Title: {name}
Genre: {narrative_voice}
Writing Style: {narrative_tone}
One-liner: {short_description}

Two paragraph pitch:"""

    PROMPT_FROM_SOURCE_STORY = """## Instructions

You are a master at summarizing stories for a publishing company.

Please take the following story fragment and condense it into three paragraphs.

Be colorful, descriptive, but clear and specific. Make sure your three paragraphs read like a narrative that includes the characters, motivations, setting, tone and voice, and plot points.

## Title

{name}

## Story

{source_story_text}

## Story Summary

Remember: You're a master at summarizing. Transform the story into three paragraphs that includes the characters, motivations, setting, tone and voice, and plot points.

Summary:"""

    @staticmethod
    def get_field() -> str:
        return "description"

    def inner_generate(
        self,
        variables: dict,
        generator: PluginInstance,
        context: AgentContext,
        generation_config: Optional[dict] = None,
    ) -> Block:
        if variables.get("source_story_text"):
            prompt = self.PROMPT_FROM_SOURCE_STORY
        else:
            prompt = self.PROMPT_NO_SOURCE_STORY

        task = generator.generate(
            text=safe_format(prompt, variables),
            streaming=True,
            append_output_to_file=True,
            make_output_public=True,
        )
        block = self.task_to_str_block(task)
        return block
