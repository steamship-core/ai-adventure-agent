import os
import urllib.request
import uuid

from PIL import Image
from steamship import Block, PluginInstance, Steamship
from steamship.agents.schema import AgentContext

from endpoints.game_state import GameState
from endpoints.server_settings import ServerSettings
from schema.characters import Item
from schema.quest import Quest
from utils.context_utils import get_profile_image_generator


class AdventureGame:
    context: AgentContext
    game_state: GameState
    server_settings: ServerSettings

    client: Steamship
    llm: PluginInstance
    image_generator: PluginInstance
    voice_generator: PluginInstance

    image_counter = 0

    def __init__(self):
        # Load Steamship library
        self.client = Steamship()
        self.client.switch_workspace(workspace_handle=f"ai-adventure-{uuid.uuid4()}")
        self.context = AgentContext.get_or_create(self.client, {"id": "default"})

        # Load settings for server, user, and quest
        self.game_state = GameState()
        self.server_settings = ServerSettings()

        self.server_settings.add_to_agent_context(self.context)

    def collect_game_state(self):
        """Long term goal: this is persistent and picks up with the user at each stage of the way."""
        self.game_state.player.name = input("What is your character's name? ")
        self.game_state.player.background = input("What's your character's backstory? ")
        item = input("What is your character's starting item? ")
        self.game_state.player.inventory.append(Item(name=item))
        self.game_state.player.motivation = input(
            "What is your character motivated to achieve? "
        )
        self.game_state.tone = input("What's the tone of the story? ")
        self.create_character_image()

    def collect_quest_settings(self) -> Quest:
        quest = Quest()
        inventory = "\n".join([item.name for item in self.game_state.player.inventory])
        print(f"\n*****\nYour current inventory is: \n{inventory}\n******")

        quest.description = input(
            f"What mission should {self.game_state.player.name} go on? "
        )
        quest.chat_history = quest.create_chat_history(
            self.client, self.game_state.player
        )

        return quest

    def embark_on_quest(self, quest: Quest):
        """Intention: this eventually picks up on the right next part until the quest is complete."""

        # Generate setting image
        quest.chat_history.append_system_message(
            f"{self.game_state.player.name} is about to go on a mission to {quest}.  Describe the setting using visually descriptive words."
        )
        setting_description = (
            self.llm.generate(quest.chat_history.file.id, options={"max_tokens": 100})
            .wait()
            .blocks[0]
            .text[:1000]
        )
        setting_image_block = self.generate_image_block(setting_description)
        self.show_image(setting_image_block)

        # First part of the mission
        quest.chat_history.append_system_message(
            "Describe the first few things they do in a few sentences."
        )
        first_part = self.llm.generate(quest.chat_history.file.id).wait().blocks[0].text
        print(first_part)
        quest.chat_history.append_assistant_message(first_part)

        # Problem generation / user solution
        quest.chat_history.append_system_message(
            f"What problem did {self.game_state.player.name} encounter next? "
        )
        problem = self.llm.generate(quest.chat_history.file.id).wait().blocks[0].text
        quest.chat_history.append_system_message(
            f"{self.game_state.player.name} encountered a problem: {problem}"
        )
        solution = input(
            f"\n*****\nOh no! {self.game_state.player.name} has a problem: {problem}. \nWhat should {self.game_state.player.name} do? "
        )
        quest.chat_history.append_system_message(
            f"{self.game_state.player.name} solved that by {solution}. What happens next? "
        )
        next_part = self.llm.generate(quest.chat_history.file.id).wait().blocks[0].text
        print(next_part)
        quest.chat_history.append_assistant_message(next_part)

        # Last part of the mission
        quest.chat_history.append_system_message(
            f"How does this mission end? {self.game_state.player.name} should not yet achieve their overall goal of {self.game_state.player.motivation}"
        )
        last_part = self.llm.generate(quest.chat_history.file.id).wait().blocks[0].text
        print(last_part)
        quest.chat_history.append_assistant_message(last_part)

        quest.chat_history.append_system_message(
            f"What object or item did {self.game_state.player.name} find during that story? It should fit the setting of the story and help {self.game_state.player.name} achieve their goal. Please respond only with ITEM NAME: <name> ITEM DESCRIPTION: <description>"
        )
        item = (
            self.llm.generate(quest.chat_history.file.id, options={"max_tokens": 100})
            .wait()
            .blocks[0]
            .text
        )
        print(f"{self.game_state.player.name} found an item!\n{item}")
        item_pic_block = self.generate_image_block(item)
        self.show_image(item_pic_block)
        self.game_state.player.inventory += Item(name=item)

        # Build summary for next mission
        quest.chat_history.append_system_message(
            "Summarize this mission in three sentences."
        )
        summary = (
            self.llm.generate(quest.chat_history.file.id, options={"max_tokens": 200})
            .wait()
            .blocks[0]
            .text
        )

        self.game_state.quests.append(Quest(text_summary=summary))

        return quest

    def generate_image_block(self, text: str) -> Block:
        return (
            get_profile_image_generator(self.context)
            .generate(
                text=text[:1000], make_output_public=True, append_output_to_file=True
            )
            .wait()
            .blocks[0]
        )

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
            self.game_state.player.description = input(
                f"Describe {self.game_state.player.name}'s appearance: "
            )
            new_pic_block = self.generate_image_block(
                self.game_state.player.description
            )
            self.show_image(new_pic_block)
            response = input(
                f"Does {self.game_state.player.name} look like that (y/n)? "
            )
            accepted = response.lower() == "y"

    def game_loop(self):
        """The main game loop."""
        self.collect_game_state()

        while True:
            # Start a single mission
            quest = self.collect_quest_settings()
            self.embark_on_quest(quest)


if __name__ == "__main__":
    AdventureGame().game_loop()
