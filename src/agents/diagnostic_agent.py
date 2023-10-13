from enum import Enum
from typing import List

from steamship import Block, Tag
from steamship.agents.schema import Action, AgentContext
from steamship.agents.schema.action import FinishAction
from steamship.data import TagKind
from steamship.data.tags.tag_constants import ChatTag, RoleTag, TagValueKey

from utils.context_utils import emit
from utils.generation_utils import send_story_generation
from utils.interruptible_python_agent import InterruptiblePythonAgent
from utils.tags import QuestTag, TagKindExtensions


class DiagnosticMode(str, Enum):
    KNOCK_KNOCK = "knock-knock"


class DiagnosticAgent(InterruptiblePythonAgent):
    """
    The agent is used to test streaming.
    """

    test_name: str

    def __init__(self, test_name: str, **kwargs):
        super().__init__(tools=[], test_name=test_name, **kwargs)

    def tags(self, context_id: str) -> List[Tag]:
        return [
            Tag(
                kind=TagKind.CHAT,
                name=ChatTag.ROLE,
                value={TagValueKey.STRING_VALUE: RoleTag.ASSISTANT},
            ),
            Tag(kind=TagKind.CHAT, name=ChatTag.MESSAGE),
            # See agent_service.py::chat_history_append_func for the duplication prevention this tag results in
            Tag(kind=TagKind.CHAT, name="streamed-to-chat-history"),
            Tag(kind=TagKindExtensions.QUEST, name=QuestTag.QUEST_CONTENT),
            Tag(
                kind=TagKindExtensions.QUEST,
                name=QuestTag.QUEST_ID,
                value={"id": context_id},
            ),
        ]

    def run(self, context: AgentContext) -> Action:
        """
        It could go in a tool, but that doesn't feel necessary.. there are some other spots where tools feel very
        well fit, but this might be better left open-ended so we can stop/start things as we like.
        """
        send_story_generation(
            "Tell a knock knock joke",
            quest_name="Knock Knock",
            context=context,
        )

        blocks = [Block(text=self.test_name, tags=self.tags(self.test_name))]
        emit(blocks, context)
        return FinishAction(output=blocks)
