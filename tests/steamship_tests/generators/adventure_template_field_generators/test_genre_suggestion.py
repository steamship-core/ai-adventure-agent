import pytest
from steamship import MimeTypes, Steamship
from steamship.agents.schema import AgentContext

from generators.server_settings_field_generators.genre_generator import GenreGenerator
from utils.context_utils import get_story_text_generator


@pytest.mark.usefixtures("client")
def test_genre_suggestion(client: Steamship):
    context = AgentContext.get_or_create(
        client=client, context_keys={"id": "testing-foo"}, searchable=False
    )
    variables = {
        "name": "The Most Cheese",
        "short_description": "A chef in Italy goes on an adventure to find the cave with the most cheese.",
    }
    generator = get_story_text_generator(context)
    suggestor = GenreGenerator()
    block = suggestor.generate(variables, generator, context)
    assert block.mime_type == MimeTypes.TXT
    assert block.text
