import pytest
from steamship import MimeTypes, Steamship
from steamship.agents.schema import AgentContext

from generators.server_settings_field_generators.adventure_background_generator import (
    AdventureBackgroundGenerator,
)
from utils.context_utils import get_story_text_generator


@pytest.mark.usefixtures("client")
def test_adventure_background_suggestion(client: Steamship):
    context = AgentContext.get_or_create(
        client=client, context_keys={"id": "testing-foo"}, searchable=False
    )
    variables = {
        "name": "The Most Cheese",
        "short_description": "A chef in Italy goes on an adventure to find the cave with the most cheese.",
        "narrative_voice": "Comedy",
        "narrative_tone": "Written like a wordy movie.",
        "adventure_goal": "uncover the secret of the legendary Cheese Vault",
    }
    generator = get_story_text_generator(context)
    suggestor = AdventureBackgroundGenerator()
    block = suggestor.generate(variables, generator, context)
    assert block.mime_type == MimeTypes.TXT
    assert block.text
