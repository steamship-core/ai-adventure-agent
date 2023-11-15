from steamship import SteamshipError, Task
from steamship.agents.schema import AgentContext

from generators.utils import safe_format
from utils.context_utils import get_server_settings, get_story_text_generator

PROMPTS = {
    "narrative_voice": """Write a short genre suggestion for a story. Be creative!

Examples of good output include: fantasy adventure, children’s book, young adult novel, fanfic, high literature

Suggestion:""",
    "narrative_tone": """Write a narrative tone suggestion for a story. Be creative! But keep it concise.

Examples of god outputs include: silly, parody, dramatic, gritty, film noir, etc.""",
    "adventure_background": """Write a few notes about an scene that is to be in a short story.

Be concise but descriptive, using Markdown and bullet points. Include the sections: tone, narrative voice, characters, locations, important items, and real-world references.

## Tone

{narrative_tone}

## Narrative voice

{narrative_voice}

## Characters

- """,
    "adventure_goal": """I need help! Write a goal for a character in an riveting story. Be short! But creative and colorful. It needs to REALLY capture attention!

Examples:
- destroy the Ring of Elders
- get into Harvard
- escape from jail
- create a company and take it to IPO
- fall in love with a supermodel
- pull off the world's greatest bank heist

Goal:
-""",
}


class EditorSuggestionGenerator:
    def generate_editor_suggestion(
        self, field_name: str, unsaved_server_settings: dict, context: AgentContext
    ) -> Task:
        server_settings = get_server_settings(context)
        generator = get_story_text_generator(context)

        prompt = PROMPTS.get(field_name)

        if not prompt:
            raise SteamshipError(
                message=f"Unable to generate a suggestion for {field_name}"
            )

        # Now template it against the saved server settings
        variables = server_settings.dict()
        variables.update(unsaved_server_settings)

        templated_prompt = safe_format(prompt, variables)

        task = generator.generate(
            text=templated_prompt,
            streaming=True,
            append_output_to_file=True,
            make_output_public=True,
        )
        task.wait()
        return task
