from typing import List, Optional

from steamship import Block, Steamship, SteamshipError
from steamship.agents.service.agent_service import AgentService
from steamship.data.tags.tag_constants import RoleTag
from steamship.invocable import post
from steamship.invocable.package_mixin import PackageMixin

from tools.end_quest_tool import EndQuestTool
from tools.start_quest_tool import StartQuestTool

# An instnace is a game instance.
from utils.context_utils import get_audio_narration_generator, get_game_state
from utils.tags import QuestTag, TagKindExtensions


class QuestMixin(PackageMixin):
    """Provides endpoints for Game State."""

    client: Steamship
    agent_service: AgentService

    def __init__(self, client: Steamship, agent_service: AgentService):
        self.client = client
        self.agent_service = agent_service

    @post("/start_quest")
    def start_quest(self, purpose: Optional[str] = None, **kwargs) -> dict:
        """Starts a quest."""
        context = self.agent_service.build_default_context()
        game_state = get_game_state(context)
        quest_tool = StartQuestTool()
        quest = quest_tool.start_quest(game_state, context, purpose)

        return quest.dict()

    @post("/end_quest")
    def end_quest(self, **kwargs) -> str:
        """Starts a quest."""
        context = self.agent_service.build_default_context()
        game_state = get_game_state(context)
        quest_tool = EndQuestTool()
        return quest_tool.end_quest(game_state, context)

    @post("/get_quest")
    def get_quest(self, quest_id: str, **kwargs) -> List[dict]:
        """Gets the blocks for an existing quest."""
        context = self.agent_service.build_default_context()
        blocks = []

        def matches_quest(_block: Block, _quest_id: str) -> bool:
            for tag in _block.tags or []:
                if (
                    tag.kind == TagKindExtensions.QUEST
                    and tag.name == QuestTag.QUEST_ID
                    and (tag.value or {}).get("id").lower() == _quest_id.lower()
                ):
                    return True
            return False

        if (
            context.chat_history
            and context.chat_history.file
            and context.chat_history.file.blocks
        ):
            for block in context.chat_history.file.blocks:
                if matches_quest(block, quest_id):
                    blocks.append(block)

        return [block.dict(by_alias=True) for block in blocks]

    @post("/narrate_block")
    def narrate_block(self, block_id: str, **kwargs) -> dict:
        """Returns a streaming narration for a block."""
        block = Block.get(self.client, _id=block_id)

        # Only narrate if it's actually
        if not block.is_text():
            raise SteamshipError(
                message=f"Block {block_id} is not a text block. Unable to narrate."
            )

        chat_role = block.chat_role
        if chat_role not in [RoleTag.ASSISTANT, RoleTag.USER]:
            raise SteamshipError(
                message=f"Block {block_id} did not have the chat role of assistant or user. Unable to narrate."
            )

        context = self.agent_service.build_default_context()

        narration_model = get_audio_narration_generator(context)
        generation = narration_model.generate(
            text=block.text,
            make_output_public=True,
            append_output_to_file=True,
            streaming=True,
        )

        # TODO: Does this await the completion of the entire thing?
        generation.wait()

        if not generation.output or not generation.output.blocks:
            raise SteamshipError(
                message="Streaming audio generation did not produce output. Unable to narrate."
            )

        block = generation.output.blocks[0]

        return {"url": block.to_public_url()}
