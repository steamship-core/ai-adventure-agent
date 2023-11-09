import pytest
from steamship import Steamship, TaskState
from steamship.agents.schema import AgentContext

from generators.image_generators.stable_diffusion_with_loras import (
    StableDiffusionWithLorasImageGenerator,
)
from utils.context_utils import (
    get_game_state,
    get_server_settings,
    save_server_settings,
)


@pytest.mark.usefixtures("client")
def test_profile_pic_generation(client: Steamship):
    context = AgentContext.get_or_create(
        client=client, context_keys={"id": "testing-foo"}, searchable=False
    )
    gs = get_game_state(context)

    gs.player.name = "PICKLE MAN"
    gs.player.description = "A pickle as tall as a building that wears suspenders."

    ss = get_server_settings(context)
    ss.profile_image_theme = "pixel_art_3"

    ss.profile_image_prompt = "Richard Stallman at y combinator headquarters"
    save_server_settings(ss, context)

    generator = StableDiffusionWithLorasImageGenerator()

    task = generator.request_profile_image_generation(context)

    task.wait()
    assert task.state == TaskState.succeeded
    assert task.output
    assert task.output.blocks
    assert task.output.blocks[0].id

    url = f"{client.config.api_base}block/{task.output.blocks[0].id}/raw"
    assert url
