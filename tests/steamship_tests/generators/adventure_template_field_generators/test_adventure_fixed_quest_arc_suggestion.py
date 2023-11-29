import json

import pytest
from steamship import MimeTypes, Steamship
from steamship.agents.schema import AgentContext

from generators.server_settings_field_generators.adventure_fixed_quest_arc_generator import (
    AdventureFixedQuestArcGenerator,
)
from utils.context_utils import get_story_text_generator


@pytest.mark.usefixtures("client")
def test_adventure_quest_arc_suggestion(client: Steamship):
    context = AgentContext.get_or_create(
        client=client, context_keys={"id": "testing-foo"}, searchable=False
    )
    variables = {
        "name": "Wild Whiskers",
        "description": """A cat has to learn to mountain climb to reach the top of Mt. Everest.""",
    }
    generator = get_story_text_generator(context)
    suggestor = AdventureFixedQuestArcGenerator()
    block = suggestor.generate(variables, generator, context)
    assert block.mime_type == MimeTypes.JSON
    thelist = json.loads(block.text)
    assert isinstance(thelist, list)
    assert len(thelist)
    assert block.text
