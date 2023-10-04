from steamship import MimeTypes
from steamship.agents.schema import Action, Agent, AgentContext
from steamship.agents.schema.action import FinishAction
from steamship.data import Block

from game_agent.script import Script
from game_agent.tags import CharacterTag, SceneTag


class GameAgent(Agent):
    """
    GOAL: Implement an agent that streams back things.
    """

    PROMPT = ""

    def next_action(self, context: AgentContext) -> Action:
        script = Script(context.chat_history)

        script.append_scene_action(SceneTag.START)
        print("1")
        script.append_scene_action(
            SceneTag.BACKGROUND,
            url="https://picsum.photos/200/300",
            mime_type=MimeTypes.JPG,
        )
        print("2")
        script.append_character_action(
            CharacterTag.IMAGE,
            url="https://picsum.photos/200/200",
            mime_type=MimeTypes.JPG,
        )
        print("3")
        script.append_assistant_message(
            text="This is an intermediate assistant message", mime_type=MimeTypes.MKD
        )
        print("4")
        return FinishAction(
            output=[
                Block(
                    text="This is the final assistant message.", mime_type=MimeTypes.MKD
                )
            ]
        )
