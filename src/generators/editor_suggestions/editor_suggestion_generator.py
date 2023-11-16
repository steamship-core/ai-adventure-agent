from steamship import SteamshipError, Task
from steamship.agents.schema import AgentContext

from generators.utils import safe_format
from utils.context_utils import get_server_settings, get_story_text_generator

PROMPTS = {
    # Note: this is "genre" in the UI
    "narrative_voice": """Write a short genre suggestion for a story. Be expansive, creative, but concise!

Examples of good outputs:

- fantasy adventure
- children’s book
- young adult novel
- fanfic
- high literature

Suggestion:

-""",
    # Note: this is "writing style"
    "narrative_tone": """Write a narrative tone suggestion for a story with the genre {narrative_voice}. Be creative! Wide-ranging! But keep it concise.

Examples of good outputs:

- silly, like a Cartoon Network show
- parody, in the style of an HBO show
- dramatic, with a tinge of danger
- gritty, high contrast and real
- film noir, with a romantic tinge of hard-boiled mystery

Suggestion:

-""",
    "adventure_background": """I need help! Write a few notes for a director about an scene in a short story.

Be colorful, descriptive, but concise! Use Markdown and bullet points. Include the sections: tone, narrative voice, adventure background story, non-protagonist characters, locations, and important items to the story.

## Genre

{narrative_voice}

## Writing Style

{narrative_tone}

""",
    "adventure_goal": """I need help! Finish the main character goal for this short story.

Be short! But creative and colorful. It needs to REALLY capture attention!

Examples of riveting goals:
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
