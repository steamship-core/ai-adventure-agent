from typing import List

from steamship import Block, Steamship
from steamship.agents.service.agent_service import AgentService
from steamship.invocable import post
from steamship.invocable.package_mixin import PackageMixin


class CampMixin(PackageMixin):
    """Provides endpoints for the Camp."""

    client: Steamship
    agent_service: AgentService

    def __init__(self, client: Steamship, agent_service: AgentService):
        self.client = client
        self.agent_service = agent_service

    @post("/get_camp_blocks")
    def get_camp_blocks(self, **kwargs) -> List[dict]:
        """Gets the blocks for the camp."""
        context = self.agent_service.build_default_context()
        blocks = []

        def matches_camp(_block: Block) -> bool:
            for tag in _block.tags or []:
                if tag.kind and tag.kind.lower() == "camp":
                    return True
                if tag.name and tag.name.lower() == "camp":
                    return True
            return False

        if (
            context.chat_history
            and context.chat_history.file
            and context.chat_history.file.blocks
        ):
            for block in context.chat_history.file.blocks:
                if matches_camp(block):
                    blocks.append(block)

        return [block.dict(by_alias=True) for block in blocks]
