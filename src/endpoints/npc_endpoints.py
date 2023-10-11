from typing import List

from steamship import Steamship
from steamship.agents.service.agent_service import AgentService
from steamship.invocable import post
from steamship.invocable.package_mixin import PackageMixin

from schema.objects import TradeResult
from tools.end_conversation_tool import EndConversationTool
from tools.start_conversation_tool import StartConversationTool

# An instnace is a game instance.
from tools.trade_tool import TradeTool
from utils.context_utils import get_game_state


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

        npc = None

        if game_state.camp and game_state.camp.npcs:
            for _npc in game_state.camp.npcs:
                if _npc.name == counter_party:
                    npc = _npc
                    break

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
