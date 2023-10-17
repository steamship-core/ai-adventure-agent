import uuid
from datetime import datetime, timezone
from typing import List

from steamship import Steamship
from steamship.agents.service.agent_service import AgentService
from steamship.invocable import post
from steamship.invocable.package_mixin import PackageMixin

from schema.objects import TradeResult, Item
from tools.end_conversation_tool import EndConversationTool
from tools.start_conversation_tool import StartConversationTool

# An instnace is a game instance.
from tools.trade_tool import TradeTool
from utils.context_utils import get_game_state, save_game_state
from utils.generation_utils import generate_merchant_inventory


class NpcMixin(PackageMixin):
    """Provides endpoints for NPC Transitions."""

    client: Steamship
    agent_service: AgentService

    def __init__(self, client: Steamship, agent_service: AgentService):
        self.client = client
        self.agent_service = agent_service

    @post("/start_conversation")
    def start_conversation(self, character_name: str, **kwargs) -> dict:
        """Starts a conversation with the NPC by the provided name."""
        context = self.agent_service.build_default_context()
        game_state = get_game_state(context)
        tool = StartConversationTool()
        convo_or_error = tool.start_conversation(character_name, game_state, context)
        if isinstance(convo_or_error, str):
            return {"error": True, "message": convo_or_error}
        return convo_or_error.dict()

    @post("/end_conversation")
    def end_conversation(self, **kwargs) -> dict:
        """Starts a conversation with the NPC by the provided name."""
        context = self.agent_service.build_default_context()
        game_state = get_game_state(context)
        tool = EndConversationTool()
        response = tool.end_conversation(game_state, context)
        return {"message": response}

    @post("/trade")
    def trade(
        self, counter_party: str, sell: List[str] = None, buy: List[str] = None
    ) -> dict:
        """Starts a conversation with the NPC by the provided name."""
        context = self.agent_service.build_default_context()
        game_state = get_game_state(context)

        npc = game_state.find_npc(counter_party)

        if not npc:
            return TradeResult(
                player_name=game_state.player.name,
                player_gold=game_state.player.gold,
                player_gold_delta=0,
                counterparty_name=counter_party,
                error_message=f'Unable to find "{counter_party}" at camp. Are you sure you\'re referencing them by name?',
            ).dict()

        tool = TradeTool(counter_party=npc)
        result = tool.attempt_trade(
            game_state=game_state,
            context=context,
            player_seeks_to_sell=sell,
            player_seeks_to_buy=buy,
        )
        return result.dict()

    @post("/refresh_inventory")
    def trade(
            self, npc_name: str
    ) -> List[Item]:
        """Starts a conversation with the NPC by the provided name."""
        context = self.agent_service.build_default_context()
        game_state = get_game_state(context)

        generated_items = generate_merchant_inventory(game_state.player, context=context)
        # refresh game state directly before altering
        game_state = get_game_state(context)
        npc = game_state.find_npc(npc_name)
        npc.inventory = []
        npc.inventory_last_updated = datetime.now(timezone.utc).isoformat()
        for item in generated_items:
            npc.inventory.append(Item(
                name=item[0],
                description=item[1],
                id=str(uuid.uuid4())
            ))
        save_game_state(game_state, context)
        return npc.inventory


