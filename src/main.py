import os
import urllib.request

from PIL import Image
from steamship import Block, PluginInstance, Steamship

from game_agent import GameAgent
from schema import Quest, ServerSettings, UserSettings


class AdventureGame(GameAgent):
    tone: str
    motivation: str

    user_settings: UserSettings
    server_settings: ServerSettings

    llm: PluginInstance
    image_generator: PluginInstance
    voice_generator: PluginInstance

    image_counter = 0

    def __init__(self, client: Steamship, id: str):
        super().__init__(client, id=id)

        # Load Steamship library
        self.client = client

        # Load settings for server, user, and quest
        self.user_settings = UserSettings()
        self.server_settings = ServerSettings()

        # Load models
        self.llm = self.server_settings.get_story_generator(self.client)
        self.image_generator = self.server_settings.get_image_generator(self.client)
        self.voice_generator = self.server_settings.get_voice_generator(self.client)

    def collect_user_settings(self) -> UserSettings:
        """Long term goal: this is persistent and picks up with the user at each stage of the way."""
        self.user_settings.name = self.ask(
            "user_settings.name", "What is your character's name? "
        )
        self.user_settings.background = self.ask(
            "user_settings.background", "What's your character's backstory? "
        )
        self.user_settings.inventory = self.ask(
            "user_settings.inventory", "What is your character's starting item? "
        )

        self.user_settings.inventory += "\n"  # TODO: How do we handle this kind of programmatic post-processing of the ask?

        self.user_settings.motivation = self.ask(
            "user_settings.motivation", "What is your character motivated to achieve? "
        )
        self.user_settings.tone = self.ask(
            "user_settings.tone", "What's the tone of the story? "
        )
        self.create_character_image()

    def collect_quest_settings(self) -> Quest:
        quest = Quest()
        print(
            f"\n*****\nYour current inventory is: \n{self.user_settings.inventory}\n******"
        )

        quest.description = input(
            f"What mission should {self.user_settings.name} go on? "
        )
        quest.chat_history = quest.create_chat_history(self.client, self.user_settings)

        return quest

    def embark_on_quest(self, quest: Quest):
        """Intention: this eventually picks up on the right next part until the quest is complete."""

        # Generate setting image
        quest.chat_history.append_system_message(
            f"{self.user_settings.name} is about to go on a mission to {quest}.  Describe the setting using visually descriptive words."
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

        # Encounter a problem!
        quest.chat_history.append_system_message(
            f"What problem did {self.user_settings.name} encounter next? "
        )
        problem = self.llm.generate(quest.chat_history.file.id).wait().blocks[0].text
        quest.chat_history.append_system_message(
            f"{self.user_settings.name} encountered a problem: {problem}"
        )

        # Get the user's solution to the problem
        solution = input(
            f"\n*****\nOh no! {self.user_settings.name} has a problem: {problem}. \nWhat should {self.user_settings.name} do? "
        )
        quest.chat_history.append_system_message(
            f"{self.user_settings.name} solved that by {solution}. What happens next? "
        )
        next_part = self.llm.generate(quest.chat_history.file.id).wait().blocks[0].text
        print(next_part)
        quest.chat_history.append_assistant_message(next_part)

        # Last part of the mission
        quest.chat_history.append_system_message(
            f"How does this mission end? {self.user_settings.name} should not yet achieve their overall goal of {self.user_settings.motivation}"
        )
        last_part = self.llm.generate(quest.chat_history.file.id).wait().blocks[0].text
        print(last_part)
        quest.chat_history.append_assistant_message(last_part)

        quest.chat_history.append_system_message(
            f"What object or item did {self.user_settings.name} find during that story? It should fit the setting of the story and help {self.user_settings.name} achieve their goal. Please respond only with ITEM NAME: <name> ITEM DESCRIPTION: <description>"
        )
        item = (
            self.llm.generate(quest.chat_history.file.id, options={"max_tokens": 100})
            .wait()
            .blocks[0]
            .text
        )
        print(f"{self.user_settings.name} found an item!\n{item}")
        item_pic_block = self.generate_image_block(item)
        self.show_image(item_pic_block)
        self.user_settings.inventory += item

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

        self.user_settings.mission_summaries.append(summary)
        return quest

    def generate_image_block(self, text: str) -> Block:
        return (
            self.image_generator.generate(
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
        accepted = self.get_bool("user_settings.description_accepted", False)
        while not accepted:
            # Note on the second time through it would be better to let them edit the previous description, but there's no easy way to do this in python CLI
            self.user_settings.description = self.ask(
                "user_settings.description",
                f"Describe {self.user_settings.name}'s appearance: ",
                skip_cache=True,
            )

            new_pic_block = self.generate_image_block(self.user_settings.description)
            self.show_image(new_pic_block)
            response = input(f"Does {self.user_settings.name} look like that (y/n)? ")
            accepted = self.set_bool(
                "user_settings.description_accepted", response.lower() == "y"
            )

            if accepted:
                self.user_settings.image_url = self.set_string(
                    "user_settings.image_url", new_pic_block.raw_data_url
                )

    def game_loop(self):
        """The main game loop."""
        self.collect_user_settings()

        while True:
            # Start a single mission
            quest = self.collect_quest_settings()
            self.embark_on_quest(quest)


if __name__ == "__main__":
    # Workspace for data caching.
    workspace = "ai-game-1"

    # Note -- if you want to create a new random workspace each time, uncomment the following lines:
    # workspace = f"{workspace}-uuid.uuid4()"

    client = Steamship(workspace=workspace)

    # Create the resumable data context
    AdventureGame(client, "default").game_loop()
