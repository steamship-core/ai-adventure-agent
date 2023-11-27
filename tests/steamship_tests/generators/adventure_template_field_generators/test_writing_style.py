import pytest
from steamship import MimeTypes, Steamship
from steamship.agents.schema import AgentContext

from generators.adventure_template_field_generators.writing_style_generator import (
    WritingStyleGenerator,
)
from utils.context_utils import get_story_text_generator


@pytest.mark.usefixtures("client")
def test_writing_style_suggestion(client: Steamship):
    context = AgentContext.get_or_create(
        client=client, context_keys={"id": "testing-foo"}, searchable=False
    )
    variables = {
        "narrative_voice": "Cyberpunk",
    }
    generator = get_story_text_generator(context)
    suggestor = WritingStyleGenerator()
    block = suggestor.generate(variables, generator, context)
    assert block.mime_type == MimeTypes.TXT
    assert block.text
