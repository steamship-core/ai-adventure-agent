import pytest
from steamship import MimeTypes, Steamship
from steamship.agents.schema import AgentContext

from generators.adventure_template_field_generators.adventure_description_suggestion import (
    AdventureDescriptionSuggestionGenerator,
)
from utils.context_utils import get_story_text_generator


@pytest.mark.usefixtures("client")
def test_adventure_description_suggestion(client: Steamship):
    context = AgentContext.get_or_create(
        client=client, context_keys={"id": "testing-foo"}, searchable=False
    )
    variables = {
        "name": "The Most Cheese",
        "short_description": "A chef in Italy goes on an adventure to find the cave with the most cheese.",
    }
    generator = get_story_text_generator(context)
    suggestor = AdventureDescriptionSuggestionGenerator()
    block = suggestor.suggest(variables, generator, context)
    assert block.mime_type == MimeTypes.TXT
    assert block.text
