from steamship import File, Steamship, Block, Tag
from steamship.agents.schema import AgentContext
from steamship.data.tags.tag_constants import ChatTag, RoleTag, TagKind, TagValueKey

from agents.onboarding_agent import OnboardingAgent
from api import AdventureGameService
from endpoints.npc_endpoints import NpcMixin
from endpoints.quest_endpoints import QuestMixin
from schema.camp import Camp
from schema.characters import HumanCharacter, NpcCharacter
from schema.game_state import GameState
from schema.objects import Item
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


def test_merchant_inventory_endpoint():
    with Steamship.temporary_workspace() as client:
        context, game_state = prepare_state(client)
        result = NpcMixin._refresh_inventory(context, game_state, "merchant")
        print(result)


def test_audio_narration():
    with Steamship.temporary_workspace() as client:
        context, game_state = prepare_state(client)
        file = File.create(client, blocks=[Block(text="Let's go on an adventure! "*20, tags=[Tag(kind=TagKind.CHAT, name=ChatTag.ROLE, value={TagValueKey.STRING_VALUE : RoleTag.ASSISTANT})])])
        block = file.blocks[0]
        narration_block = QuestMixin._narrate_block(block, context)
        url = narration_block.raw_data_url
        assert narration_block.raw_data_url is not None
        print(narration_block.raw_data_url)


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
    game_state.camp = Camp()
    game_state.camp.npcs = [NpcCharacter(name="merchant", category="merchant", inventory=[Item(name="thingy",description="a thingy")])]
    save_game_state(game_state, context=context)

    return game_state

def run_onboarding(context: AgentContext):
    agent = OnboardingAgent(tools=[])
    try:
        agent.run(context)
    except RunNextAgentException:
        pass

