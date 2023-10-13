from steamship import File, Steamship
from steamship.agents.schema import AgentContext

from schema.server_settings import ServerSettings
from utils.context_utils import with_server_settings
from utils.generation_utils import send_story_generation


# @pytest.mark.usefixtures("client")
def test_send_story_generation(
    # client: Steamship
):
    with Steamship.temporary_workspace() as client:
        ctx_keys = {"id": "testing-foo"}
        ctx = AgentContext.get_or_create(
            client=client, context_keys=ctx_keys, searchable=False
        )
        ctx = with_server_settings(ServerSettings(), ctx)

        _block = send_story_generation(
            "Tell me a knock-knock joke.",
            context=ctx,
        )
        print(_block)

        f = File.get(client, ctx.chat_history.file.id)
        assert len(f.blocks) == 1
        assert len(f.blocks[0].tags) == 1

        assert f.blocks[0].tags[0].kind == "role"
        assert f.blocks[0].tags[0].name == "assistant"

        print(f)
