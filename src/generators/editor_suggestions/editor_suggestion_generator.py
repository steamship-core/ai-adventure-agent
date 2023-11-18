from typing import List

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
    "characters.name": """Suggest the name of Character #{this_index} in a story.

Story Name: {name}
Story Genre: {narrative_voice}
Story Goal: {adventure_goal}
Character ${this_index} name:""",
    "characters.tagline": """Suggest short, 5-10 word tagline of Character #{this_index} in a story.

Examples of good taglines illustrate the character's main motivation or struggle, ike this:

- (Karate Girl) Knows the ropes. But does she know herself?
- (Lawyer Sue) Sue everyone.
- (Mr. Meatball) Become the biggest meatball.
- (Dragonmaster) Ascend to the throne

Story Name: {name}
Story Genre: {narrative_voice}
Story Goal: {adventure_goal}
Character ${this_index} tagline: (${this_name}) """,
    "characters.description": """Write notes for a novel character in markdown. Be concise but colorful. Use a few bullet points per section.

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

## Appearance""",
    "characters.background": """Write notes for a novel character's background in markdown. The the character's goals are already developed.. the background should provide a riveting story of progress toward those goals!

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

## Background""",
}


class EditorSuggestionGenerator:
    def generate_editor_suggestion(
        self,
        field_name: str,
        unsaved_server_settings: dict,
        field_key_path: List,
        context: AgentContext,
    ) -> Task:
        server_settings = get_server_settings(context)
        generator = get_story_text_generator(context)

        if len(field_key_path) == 1:
            prompt_key = field_key_path[0]
        elif len(field_key_path) == 3:
            prompt_key = f"{field_key_path[0]}.{field_key_path[2]}"
        else:
            prompt_key = field_name

        prompt = PROMPTS.get(prompt_key)

        if not prompt:
            kp = ".".join(map(lambda x: f"{x}", field_key_path))
            raise SteamshipError(
                message=f"Unable to generate a suggestion for: {kp}. Lookup key: {prompt_key}"
            )

        # Now template it against the saved server settings
        variables = server_settings.dict()
        variables.update(unsaved_server_settings)

        # The template interpolation assumes a FLAT object. But the object we're working with
        # here might involve something nested (like the 3rd character). So we'll look at the keypath
        # and lift those up to be represented as this_FIELD in the parent.
        #
        # That means the prompt can utilize this_{var} inside it.
        if field_key_path and len(field_key_path) == 3:
            # we'll just hard-code in the case for: [LIST_NAME, index, FIELD]
            the_list = variables.get(field_key_path[0])
            index = field_key_path[1]
            if the_list and index < len(the_list):
                variables["this_index"] = f"{index}"
                for key in the_list[index]:
                    variables[f"this_{key}"] = the_list[index][key]

        templated_prompt = safe_format(prompt, variables)

        task = generator.generate(
            text=templated_prompt,
            streaming=True,
            append_output_to_file=True,
            make_output_public=True,
        )
        task.wait()
        return task
