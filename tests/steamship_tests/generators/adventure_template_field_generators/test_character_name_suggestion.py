import pytest
from steamship import MimeTypes, Steamship
from steamship.agents.schema import AgentContext

from generators.adventure_template_field_generators.character_name_generator import (
    CharacterNameGenerator,
)
from utils.context_utils import get_story_text_generator


@pytest.mark.usefixtures("client")
def test_character_name_suggestion_no_background(client: Steamship):
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
    }
    generator = get_story_text_generator(context)
    suggestor = CharacterNameGenerator()
    block = suggestor.generate(variables, generator, context)
    assert block.mime_type == MimeTypes.TXT
    assert block.text


@pytest.mark.usefixtures("client")
def test_character_name_suggestion_background(client: Steamship):
    context = AgentContext.get_or_create(
        client=client, context_keys={"id": "testing-foo"}, searchable=False
    )
    variables = {
        "name": "The Most Cheese",
        "short_description": "A chef in Italy goes on an adventure to find the cave with the most cheese.",
        "narrative_voice": "Comedy",
        "narrative_tone": "Written like a wordy movie.",
        "adventure_goal": "uncover the secret of the legendary Cheese Vault",
        "adventure_background": """##Colorful World Setting

* The picturesque countryside of Italy
* Quaint Italian villages with cobblestone streets
* Rolling hills covered in vineyards and olive groves
* An enchanting forest filled with towering pine trees and hidden caves

## Three Characters

1. Giovanni - A passionate and eccentric chef with a love for cheese. He is determined to find the legendary Cheese Vault and uncover its secrets. Giovanni is known for his flamboyant personality and impeccable taste buds.
2. Isabella - A spirited and adventurous young woman who joins Giovanni on his quest. Isabella is a skilled forager and has a deep knowledge of the local flora and fauna. Her infectious laughter and quick wit provide a refreshing balance to Giovanni's seriousness.
3. Lorenzo - A wise and enigmatic old man who serves as a guide for Giovanni and Isabella. He possesses a vast knowledge of the region's history and legends, including the whereabouts of the Cheese Vault. With his long white beard and twinkling eyes, Lorenzo exudes a sense of mystery and wisdom.""",
    }
    generator = get_story_text_generator(context)
    suggestor = CharacterNameGenerator()
    block = suggestor.generate(variables, generator, context)
    assert block.mime_type == MimeTypes.TXT
    assert block.text
