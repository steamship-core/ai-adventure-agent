import pytest
from steamship import MimeTypes, Steamship
from steamship.agents.schema import AgentContext

from generators.server_settings_field_generators.adventure_short_description_generator import (
    AdventureShortDescriptionGenerator,
)
from utils.context_utils import get_story_text_generator


@pytest.mark.usefixtures("client")
def test_adventure_description_suggestion(client: Steamship):
    context = AgentContext.get_or_create(
        client=client, context_keys={"id": "testing-foo"}, searchable=False
    )
    variables = {
        "name": "Wild Whiskers",
        "narrative_voice": "comedy-adventure",
        "narrative_tone": "written in a light-hearted, Pixar style manner",
    }
    generator = get_story_text_generator(context)
    suggestor = AdventureShortDescriptionGenerator()
    block = suggestor.generate(variables, generator, context)
    assert block.mime_type == MimeTypes.TXT
    assert block.text
