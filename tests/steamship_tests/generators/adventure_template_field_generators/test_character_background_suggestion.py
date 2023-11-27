import pytest
from steamship import MimeTypes, Steamship
from steamship.agents.schema import AgentContext

from generators.adventure_template_field_generators.character_background_generator import (
    CharacterBackgroundGenerator,
)
from utils.context_utils import get_story_text_generator


@pytest.mark.usefixtures("client")
def test_character_background_suggestion_no_background(client: Steamship):
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
        "this_index": "1",
        "this_name": "Mr. Meatball",
        "this_tagline": "The world's biggest meatball",
    }
    generator = get_story_text_generator(context)
    suggestor = CharacterBackgroundGenerator()
    block = suggestor.generate(variables, generator, context)
    assert block.mime_type == MimeTypes.TXT
    assert block.text
