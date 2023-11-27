import pytest
from steamship import MimeTypes, Steamship
from steamship.agents.schema import AgentContext

from generators.adventure_template_field_generators.character_description_generator import (
    CharacterDescriptionGenerator,
)
from utils.context_utils import get_story_text_generator


@pytest.mark.usefixtures("client")
def test_character_description_suggestion_no_background(client: Steamship):
    context = AgentContext.get_or_create(
        client=client, context_keys={"id": "testing-foo"}, searchable=False
    )
    variables = {
        "name": "The Most Cheese",
        "short_description": "A chef in Italy goes on an adventure to find the cave with the most cheese.",
        "narrative_voice": "Comedy",
        "narrative_tone": "Written like a wordy movie.",
        "adventure_background": "A busy and bustling neighborhood in Rome. Giovanni, the main character, leaves his job because he is entranced with finding more cheese than anyone has ever found.",
        "adventure_goal": "uncover the secret of the legendary Cheese Vault",
        "this_name": "Mr. Meatball",
        "this_tagline": "The world's biggest meatball",
        "this_background": "Mr. Meatball started life as a regular meatball, but radioactive waste spilled on him and he grew sentient",
    }
    generator = get_story_text_generator(context)
    suggestor = CharacterDescriptionGenerator()
    block = suggestor.generate(variables, generator, context)
    assert block.mime_type == MimeTypes.TXT
    assert block.text
