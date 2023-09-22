import uuid

from steamship import Steamship
from steamship.agents.schema import ChatHistory


def main():
    character_name = input("What is your character's name? ")
    character_background = input("What's your character's backstory? ")
    inventory = input("What is your character's starting item? ")
    inventory += "\n"
    quest_goal = input("What is the end goal of your character's quest? ")
    tone = input("What's the tone of the story? ")

    client = Steamship()
    generator = client.use_plugin('gpt-4', config={"model":"gpt-3.5-turbo","max_tokens": 256})
    while True:
        chat_history = chat_history_for_adventure(client, character_name, character_background, inventory, quest_goal,
                                                  tone)
        print(f"\n*****Your current inventory is: {inventory}\n******")
        quest = input(f"What mission should {character_name} go on? ")
        chat_history.append_system_message(
            f"{character_name} is about to go on a mission to {quest}.  Describe the first few things they do in a few sentences.")
        first_part = generator.generate(chat_history.file.id).wait().blocks[0].text
        print(first_part)
        chat_history.append_assistant_message(first_part)
        chat_history.append_system_message(f"What problem did {character_name} encounter next? ")
        problem = generator.generate(chat_history.file.id).wait().blocks[0].text
        chat_history.append_system_message(f"{character_name} encountered a problem: {problem}")
        solution = input(f"\n*****\nOh no! {character_name} has a problem: {problem}. \nWhat should {character_name} do? ")
        chat_history.append_system_message(f"{character_name} solved that by {solution}. What happens next? ")
        next_part = generator.generate(chat_history.file.id).wait().blocks[0].text
        print(next_part)
        chat_history.append_assistant_message(next_part)
        chat_history.append_system_message(f"How does this mission end?")
        last_part = generator.generate(chat_history.file.id).wait().blocks[0].text
        print(last_part)
        chat_history.append_assistant_message(last_part)
        chat_history.append_system_message(f"What item did {character_name} find during that adventure? Please respond only with ITEM NAME: <name> ITEM DESCRIPTION: <description>")
        item = generator.generate(chat_history.file.id).wait().blocks[0].text
        print(f"{character_name} found an item!\n{item}")
        inventory += item




def chat_history_for_adventure(client: Steamship, character_name: str, character_background: str, inventory: str,
                               quest_goal: str, tone: str):
    chat_history = ChatHistory.get_or_create(client, {"id": str(uuid.uuid4())})
    chat_history.append_system_message(
        f"We are writing a story about the adventure of a character named {character_name}.")
    chat_history.append_system_message(f"{character_name} has the following background: {character_background}")
    chat_history.append_system_message(f"{character_name} has the following things in their inventory: {inventory}")
    chat_history.append_system_message(f"{character_name}'s motivation is to {quest_goal}")
    chat_history.append_system_message(f"The tone of this story is {tone}")
    return chat_history


if __name__ == '__main__':
    main()
