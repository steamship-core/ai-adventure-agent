from typing import Dict, List

from steamship import Block, SteamshipError
from steamship.agents.schema import AgentContext

from generators.adventure_template_field_generator import (
    AdventureTemplateFieldGenerator,
)
from generators.adventure_template_field_generators.adventure_background_suggestion import (
    AdventureBackgroundSuggestionGenerator,
)
from generators.adventure_template_field_generators.adventure_description_suggestion import (
    AdventureDescriptionSuggestionGenerator,
)
from generators.adventure_template_field_generators.adventure_goal_suggestion import (
    AdventureGoalSuggestionGenerator,
)
from generators.adventure_template_field_generators.adventure_image_suggestion import (
    AdventureImageGenerator,
)
from generators.adventure_template_field_generators.adventure_name_suggestion import (
    AdventureNameSuggestionGenerator,
)
from generators.adventure_template_field_generators.adventure_short_description_suggestion import (
    AdventureShortDescriptionSuggestionGenerator,
)
from generators.adventure_template_field_generators.adventure_tag_suggestion import (
    AdventureTagSuggestionGenerator,
)
from generators.adventure_template_field_generators.character_background_suggestion import (
    CharacterBackgroundSuggestionGenerator,
)
from generators.adventure_template_field_generators.character_description_suggestion import (
    CharacterDescriptionSuggestionGenerator,
)
from generators.adventure_template_field_generators.character_image_suggestion import (
    CharacterImageSuggestionGenerator,
)
from generators.adventure_template_field_generators.character_name_suggestion import (
    CharacterNameSuggestionGenerator,
)
from generators.adventure_template_field_generators.character_tagline_suggestion import (
    CharacterTaglineSuggestionGenerator,
)
from generators.adventure_template_field_generators.narrative_tone_suggestion import (
    NarrativeToneSuggestionGenerator,
)
from generators.adventure_template_field_generators.narrative_voice_suggestion import (
    NarrativeVoiceSuggestionGenerator,
)
from utils.context_utils import get_server_settings, get_story_text_generator


class EditorSuggestionGenerator:
    PROMPTS: Dict[str, AdventureTemplateFieldGenerator] = {
        NarrativeVoiceSuggestionGenerator.get_field(): NarrativeVoiceSuggestionGenerator(),
        NarrativeToneSuggestionGenerator.get_field(): NarrativeToneSuggestionGenerator(),
        CharacterTaglineSuggestionGenerator.get_field(): CharacterTaglineSuggestionGenerator(),
        CharacterNameSuggestionGenerator.get_field(): CharacterNameSuggestionGenerator(),
        CharacterDescriptionSuggestionGenerator.get_field(): CharacterDescriptionSuggestionGenerator(),
        CharacterBackgroundSuggestionGenerator.get_field(): CharacterBackgroundSuggestionGenerator(),
        CharacterImageSuggestionGenerator.get_field(): CharacterImageSuggestionGenerator(),
        AdventureGoalSuggestionGenerator.get_field(): AdventureGoalSuggestionGenerator(),
        AdventureBackgroundSuggestionGenerator.get_field(): AdventureBackgroundSuggestionGenerator(),
        AdventureImageGenerator.get_field(): AdventureImageGenerator(),
        AdventureNameSuggestionGenerator.get_field(): AdventureNameSuggestionGenerator(),
        AdventureShortDescriptionSuggestionGenerator.get_field(): AdventureShortDescriptionSuggestionGenerator(),
        AdventureDescriptionSuggestionGenerator.get_field(): AdventureDescriptionSuggestionGenerator(),
        AdventureTagSuggestionGenerator.get_field(): AdventureTagSuggestionGenerator(),
    }

    def generate_editor_suggestion(
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
            prompt_key = f"{field_key_path[0]}.{field_name}"
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
                variables["this_index"] = f"{index}"
                for key in the_list[index]:
                    variables[f"this_{key}"] = the_list[index][key]

        block = prompt.generate(variables, generator, context)
        if not block:
            raise SteamshipError(
                message=f"Unable to generate for {field_name} - no block on output."
            )
        return block
