from steamship import Block, PluginInstance
from steamship.agents.schema import AgentContext

from generators.adventure_template_field_generator import (
    AdventureTemplateFieldGenerator,
)
from generators.utils import safe_format


class CharacterDescriptionGenerator(AdventureTemplateFieldGenerator):
    PROMPT = """Write notes for a novel character in markdown. Be concise but colorful. Use a few bullet points per section.

Include the sections: Goal, Appearance, Skills, Struggles, Quirks

# Story

## Title: {name}

## Genre

{narrative_voice}

# Character

## Name

{this_name}

## Tagline

{this_tagline}

## Goal

{adventure_goal}

## Appearance"""

    @staticmethod
    def get_field() -> str:
        return "characters.description"

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
