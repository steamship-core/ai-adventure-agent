import os
import urllib.request
import uuid
from typing import List

from steamship import Steamship, PluginInstance, Workspace, Block
from steamship.agents.schema import ChatHistory
from PIL import Image

class AdventureGame():
    character_name: str
    character_background: str
    inventory: str
    tone: str
    motivation: str

    client: Steamship
    llm: PluginInstance
    image_generator: PluginInstance

    mission_summaries: List[str]

    image_counter = 0


    def __init__(self):
        self.client = Steamship()
        self.client.switch_workspace(workspace_handle=f'ai-adventure-{uuid.uuid4()}')
        self.llm = self.client.use_plugin('gpt-4', config={"model": "gpt-3.5-turbo", "max_tokens": 256})
        self.image_generator = self.client.use_plugin("dall-e")
        self.mission_summaries = []

    def game_loop(self):
        self.character_name = input("What is your character's name? ")
        self.character_background = input("What's your character's backstory? ")
        self.inventory = input("What is your character's starting item? ")
        self.inventory += "\n"
        self.motivation = input("What is your character motivated to achieve? ")
        self.tone = input("What's the tone of the story? ")
        self.create_character_image()



        while True:
            # Start a single mission
            chat_history = self.chat_history_for_adventure()
            print(f"\n*****\nYour current inventory is: \n{self.inventory}\n******")
            quest = input(f"What mission should {self.character_name} go on? ")

            # Generate setting image
            chat_history.append_system_message(
                f"{self.character_name} is about to go on a mission to {quest}.  Describe the setting using visually descriptive words.")
            setting_description = self.llm.generate(chat_history.file.id, options={"max_tokens":100}).wait().blocks[0].text[:1000]
            setting_image_block = self.generate_image_block(setting_description)
            self.show_image(setting_image_block)

            # First part of the mission
            chat_history.append_system_message(
                f"Describe the first few things they do in a few sentences.")
            first_part = self.llm.generate(chat_history.file.id).wait().blocks[0].text
            print(first_part)
            chat_history.append_assistant_message(first_part)


            # Problem generation / user solution
            chat_history.append_system_message(f"What problem did {self.character_name} encounter next? ")
            problem = self.llm.generate(chat_history.file.id).wait().blocks[0].text
            chat_history.append_system_message(f"{self.character_name} encountered a problem: {problem}")
            solution = input(f"\n*****\nOh no! {self.character_name} has a problem: {problem}. \nWhat should {self.character_name} do? ")
            chat_history.append_system_message(f"{self.character_name} solved that by {solution}. What happens next? ")
            next_part = self.llm.generate(chat_history.file.id).wait().blocks[0].text
            print(next_part)
            chat_history.append_assistant_message(next_part)

            # Last part of the mission
            chat_history.append_system_message(f"How does this mission end? {self.character_name} should not yet achieve their overall goal of {self.motivation}")
            last_part = self.llm.generate(chat_history.file.id).wait().blocks[0].text
            print(last_part)
            chat_history.append_assistant_message(last_part)


            chat_history.append_system_message(f"What object or item did {self.character_name} find during that story? It should fit the setting of the story and help {self.character_name} achieve their goal. Please respond only with ITEM NAME: <name> ITEM DESCRIPTION: <description>")
            item = self.llm.generate(chat_history.file.id, options={"max_tokens":100}).wait().blocks[0].text
            print(f"{self.character_name} found an item!\n{item}")
            item_pic_block = self.generate_image_block(item)
            self.show_image(item_pic_block)
            self.inventory += item

            # Build summary for next mission
            chat_history.append_system_message("Summarize this mission in three sentences.")
            summary = self.llm.generate(chat_history.file.id, options={"max_tokens": 200}).wait().blocks[0].text
            self.mission_summaries.append(summary)



    def generate_image_block(self, text: str) -> Block:
        return self.image_generator.generate(text=text[:1000], make_output_public=True, append_output_to_file=True).wait().blocks[0]

    def show_image(self, block: Block):
        self.image_counter += 1
        os.makedirs("images", exist_ok=True)
        filename = f"images/image-{self.image_counter}.jpg"
        urllib.request.urlretrieve(block.raw_data_url, filename)

        image = Image.open(filename)
        image.show()

    def create_character_image(self):
        accepted = False

        while not accepted:
            # Note on the second time through it would be better to let them edit the previous description, but there's no easy way to do this in python CLI
            character_description = input(f"Describe {self.character_name}'s appearance: ")
            new_pic_block = self.generate_image_block(character_description)
            self.show_image(new_pic_block)
            response = input(f"Does {self.character_name} look like that (y/n)? ")
            accepted = response.lower() == 'y'





    def chat_history_for_adventure(self):
        chat_history = ChatHistory.get_or_create(self.client, {"id": str(uuid.uuid4())})
        chat_history.append_system_message(
            f"We are writing a story about the adventure of a character named {self.character_name}.")
        chat_history.append_system_message(f"{self.character_name} has the following background: {self.character_background}")
        chat_history.append_system_message(f"{self.character_name} has the following things in their inventory: {self.inventory}")
        chat_history.append_system_message(f"{self.character_name}'s motivation is to {self.motivation}")
        chat_history.append_system_message(f"The tone of this story is {self.tone}")
        prepared_mission_summaries = '\n'.join(self.mission_summaries)
        if len(self.mission_summaries) > 0:
            chat_history.append_system_message(f"{self.character_name} has already been on previous missions: \n {prepared_mission_summaries}")
        return chat_history


if __name__ == '__main__':
    AdventureGame().game_loop()
