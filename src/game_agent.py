from steamship.agents.schema import Action, Agent, AgentContext

from quest_agent import QuestAgent
from state_based_agent import StateBasedAgent


class GameAgent(StateBasedAgent):
   """
   GOAL: Implement an agent that streams back things.
   """

   PROMPT = ""

   def start(self, context: AgentContext) -> str:
       print("let's begin!")
       print("What's your name?")
       return "receive_name"

   def receive_name(self, context: AgentContext) -> str:
       print(f"Hi {context.chat_history.last_user_message.text}")
       print("What's your favorite color?")
       return "receive_color"

   def receive_color(self, context: AgentContext) -> str:
       print(f"Cool your favorite color is  {context.chat_history.last_user_message.text}")
       print("Do you like loops?")
       return "loop"

   def loop(self, context: AgentContext) -> str:
       response = context.chat_history.last_user_message.text.lower()
       if response == "yes" or response == "y":
           print("So do I!")
           print("Do you like loops?")
           return "loop"
       else:
           print("Ok")
           return self.FINISHED
