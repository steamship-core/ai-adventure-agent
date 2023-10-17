from steamship import File, Steamship
from steamship.agents.schema import AgentContext

from agents.onboarding_agent import OnboardingAgent
from schema.characters import HumanCharacter
from schema.game_state import GameState
from schema.server_settings import ServerSettings
from utils.context_utils import with_server_settings, _GAME_STATE_KEY, save_game_state, RunNextAgentException
from utils.generation_utils import send_story_generation, generate_merchant_inventory, generate_quest_arc


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
            quest_name="test-quest",
            context=ctx,
        )
        print(_block)

        f = File.get(client, ctx.chat_history.file.id)
        assert len(f.blocks) == 2
        assert len(f.blocks[1].tags) == 6

        sorted_tags = sorted(f.blocks[1].tags, key=lambda x: x.kind + x.name)

        assert sorted_tags[3].kind == "quest"
        assert sorted_tags[3].name == "quest_content"

        assert sorted_tags[4].kind == "quest"
        assert sorted_tags[4].name == "quest_id"
        assert sorted_tags[4].value == {"id":"test-quest"}

        assert sorted_tags[5].kind == "role"
        assert sorted_tags[5].name == "assistant"

        print(f)


def test_merchant_inventory():
    with Steamship.temporary_workspace() as client:
        context, game_state = prepare_state(client)
        inventory = generate_merchant_inventory(player=game_state.player, context=context)

        assert len(inventory) == 5
        for item in inventory:
            # name length is less than description length
            assert len(item[0]) < len(item[1])


def test_quest_arc():
    with Steamship.temporary_workspace() as client:
        context, game_state = prepare_state(client)
        quest_arc = generate_quest_arc(player=game_state.player, context=context)

        assert len(quest_arc) > 8
        for quest_description in quest_arc:
            assert quest_description.goal is not None
            assert quest_description.location is not None

def prepare_state(client: Steamship) -> (AgentContext, GameState):
    ctx_keys = {"id": "testing-foo"}
    ctx = AgentContext.get_or_create(
        client=client, context_keys=ctx_keys, searchable=False
    )
    ctx = with_server_settings(ServerSettings(), ctx)
    game_state = create_test_game_state(ctx)
    run_onboarding(ctx)
    return ctx, game_state

def create_test_game_state(context: AgentContext) -> GameState:
    game_state = GameState()
    context.metadata[_GAME_STATE_KEY] = game_state

    game_state.player = HumanCharacter()
    game_state.player.name = "Dave"
    game_state.player.motivation = "Going to space"
    game_state.player.description = "he is tall"
    game_state.player.background = "he's a guy"
    game_state.tone = "funny"
    game_state.genre = "adventure"
    save_game_state(game_state, context=context)

    return game_state

def run_onboarding(context: AgentContext):
    agent = OnboardingAgent(tools=[])
    try:
        agent.run(context)
    except RunNextAgentException:
        pass

