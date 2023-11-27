from typing import Dict, List

from steamship import Block, SteamshipError
from steamship.agents.schema import AgentContext

from generators.adventure_template_field_generator import (
    AdventureTemplateFieldGenerator,
)
from generators.adventure_template_field_generators.adventure_background_generator import (
    AdventureBackgroundGenerator,
)
from generators.adventure_template_field_generators.adventure_description_generator import (
    AdventureDescriptionGenerator,
)
from generators.adventure_template_field_generators.adventure_goal_generator import (
    AdventureGoalGenerator,
)
from generators.adventure_template_field_generators.adventure_image_generator import (
    AdventureImageGenerator,
)
from generators.adventure_template_field_generators.adventure_name_generator import (
    AdventureNameGenerator,
)
from generators.adventure_template_field_generators.adventure_short_description_generator import (
    AdventureShortDescriptionGenerator,
)
from generators.adventure_template_field_generators.adventure_tag_generator import (
    AdventureTagGenerator,
)
from generators.adventure_template_field_generators.character_background_generator import (
    CharacterBackgroundGenerator,
)
from generators.adventure_template_field_generators.character_description_generator import (
    CharacterDescriptionGenerator,
)
from generators.adventure_template_field_generators.character_image_generator import (
    CharacterImageGenerator,
)
from generators.adventure_template_field_generators.character_name_generator import (
    CharacterNameGenerator,
)
from generators.adventure_template_field_generators.character_tagline_generator import (
    CharacterTaglineGenerator,
)
from generators.adventure_template_field_generators.genre_generator import (
    GenreGenerator,
)
from generators.adventure_template_field_generators.writing_style_generator import (
    WritingStyleGenerator,
)
from utils.context_utils import get_server_settings, get_story_text_generator


class EditorSuggestionGenerator:
    PROMPTS: Dict[str, AdventureTemplateFieldGenerator] = {
        GenreGenerator.get_field(): GenreGenerator(),
        WritingStyleGenerator.get_field(): WritingStyleGenerator(),
        CharacterTaglineGenerator.get_field(): CharacterTaglineGenerator(),
        CharacterNameGenerator.get_field(): CharacterNameGenerator(),
        CharacterTaglineGenerator.get_field(): CharacterTaglineGenerator(),
        CharacterDescriptionGenerator.get_field(): CharacterDescriptionGenerator(),
        CharacterBackgroundGenerator.get_field(): CharacterBackgroundGenerator(),
        CharacterImageGenerator.get_field(): CharacterImageGenerator(),
        AdventureGoalGenerator.get_field(): AdventureGoalGenerator(),
        AdventureBackgroundGenerator.get_field(): AdventureBackgroundGenerator(),
        AdventureImageGenerator.get_field(): AdventureImageGenerator(),
        AdventureNameGenerator.get_field(): AdventureNameGenerator(),
        AdventureShortDescriptionGenerator.get_field(): AdventureShortDescriptionGenerator(),
        AdventureDescriptionGenerator.get_field(): AdventureDescriptionGenerator(),
        AdventureTagGenerator.get_field(): AdventureTagGenerator(),
    }

    def generate(
        self,
        field_name: str,
        unsaved_server_settings: dict,
        field_key_path: List,
        context: AgentContext,
    ) -> Block:
        server_settings = get_server_settings(context)
        generator = get_story_text_generator(context)
        if not field_key_path:
            prompt_key = field_name
        elif len(field_key_path) == 1:
            prompt_key = field_name
        elif len(field_key_path) == 3:
            prompt_key = f"{field_key_path[0]}.{field_key_path[2]}"
        else:
            prompt_key = field_name

        prompt = self.PROMPTS.get(prompt_key)

        if not prompt:
            if field_key_path:
                kp = ".".join(map(lambda x: f"{x}", field_key_path))
            else:
                kp = prompt_key
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
                # We 1-index it since this is to be used in prompts.
                variables["this_index"] = f"{index + 1}"
                for key in the_list[index]:
                    variables[f"this_{key}"] = the_list[index][key]

        block = prompt.generate(variables, generator, context)
        if not block:
            raise SteamshipError(
                message=f"Unable to generate for {field_name} - no block on output."
            )
        return block
