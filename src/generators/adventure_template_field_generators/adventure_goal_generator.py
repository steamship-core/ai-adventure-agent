from steamship import Block, PluginInstance
from steamship.agents.schema import AgentContext

from generators.adventure_template_field_generator import (
    AdventureTemplateFieldGenerator,
)
from generators.utils import safe_format


class AdventureGoalGenerator(AdventureTemplateFieldGenerator):
    PROMPT = """I need help! Finish the main character goal for this short story.

Be short! But creative and colorful. It needs to REALLY capture attention!

The goal should start with a verb. Examples of riveting goals:
- destroy the Ring of Elders
- get into Harvard
- escape from jail
- create a company and take it to IPO
- fall in love with a supermodel
- pull off the world's greatest bank heist

Here are the story details. Finish with the goal!

## Genre

{narrative_voice}

## Writing Style

{narrative_tone}

{adventure_background}

## Riveting Protagonist Goal:
-"""

    @staticmethod
    def get_field() -> str:
        return "adventure_goal"

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
