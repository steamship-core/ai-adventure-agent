from steamship import Block, PluginInstance
from steamship.agents.schema import AgentContext

from generators.adventure_template_field_generator import (
    AdventureTemplateFieldGenerator,
)
from generators.utils import safe_format


class CharacterBackgroundSuggestionGenerator(AdventureTemplateFieldGenerator):
    PROMPT = """Write notes for a novel character's background in markdown. The the character's goals are already developed.. the background should provide a riveting story of progress toward those goals!

Be concise but colorful. Use a few bullet points per section.

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

{this_description}

## Background"""

    @staticmethod
    def get_field() -> str:
        return "characters.background"

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
