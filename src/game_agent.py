from steamship.agents.schema import Action, Agent, AgentContext

from quest_agent import QuestAgent


class GameAgent(Agent):
    """
    GOAL: Implement an agent that streams back things.
    """

    PROMPT = ""

    def next_action(self, context: AgentContext) -> Action:
        quest_agent = QuestAgent()
        sub_agent = quest_agent.next_action(context)
        return sub_agent.next_action(context)
