import pytest
from steamship import Steamship, TaskState
from steamship.agents.schema import AgentContext

from generators.image_generators import get_image_generator
from utils.context_utils import (
    get_game_state,
    get_server_settings,
    get_theme,
    save_game_state,
    save_server_settings,
)


@pytest.mark.usefixtures("client")
def test_profile_pic_generation(client: Steamship):
    context = AgentContext.get_or_create(
        client=client, context_keys={"id": "testing-foo"}, searchable=False
    )
    gs = get_game_state(context)

    gs.player.name = "Superhero Dog"
    gs.player.description = "A golden retriever in a superman cape."
    save_game_state(gs, context)

    ss = get_server_settings(context)
    ss.profile_image_theme = "dall_e_2_neon_cyberpunk"
    ss.profile_image_prompt = (
        "{name}, {description}. Close-up on head. Gradient background."
    )
    save_server_settings(ss, context)

    theme = get_theme(ss.profile_image_theme, context)
    generator = get_image_generator(theme)
    task = generator.request_profile_image_generation(context)

    task.wait()
    assert task.state == TaskState.succeeded
    assert task.output
    assert task.output.blocks
    assert task.output.blocks[0].id

    url = f"{client.config.api_base}block/{task.output.blocks[0].id}/raw"
    assert url
