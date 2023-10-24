from abc import ABC, abstractmethod
from enum import Enum, auto

from pydantic.fields import Field, PrivateAttr
from pydantic.main import BaseModel
from steamship import PluginInstance, Steamship

from schema.game_state import GameState


class Location(BaseModel):
    name: str
    description: str


class Goal(BaseModel):
    name: str
    description: str


class Obstacle(BaseModel):
    name: str
    description: str


class Difficulty(BaseModel):
    level: int = Field(ge=0, le=100)


class Evaluation(str, Enum):
    NOT_RELATED = auto()
    OBSTACLE_NOT_OVERCOME = auto()
    OBSTACLE_OVERCOME = auto()
    QUEST_FAILED = auto()
    QUEST_SUCCEEDED = auto()

    @staticmethod
    def from_str(label):
        match label:
            case "NOT_RELATED":
                return Evaluation.NOT_RELATED
            case "OBSTACLE_NOT_OVERCOME":
                return Evaluation.OBSTACLE_NOT_OVERCOME
            case "OBSTACLE_OVERCOME":
                return Evaluation.OBSTACLE_OVERCOME
            case "QUEST_FAILED":
                return Evaluation.QUEST_FAILED
            case "QUEST_SUCCEEDED":
                return Evaluation.QUEST_SUCCEEDED
        return Evaluation.NOT_RELATED


class Item(BaseModel):
    name: str
    description: str


class QuestMaster(BaseModel, ABC):
    @abstractmethod
    def generate_location(self, game_state: GameState) -> Location:
        pass

    @abstractmethod
    def generate_quest_goal(
        self, game_state: GameState, location: Location, difficulty: Difficulty
    ) -> Goal:
        pass

    @abstractmethod
    def generate_obstacle(
        self,
        game_state: GameState,
        location: Location,
        goal: Goal,
        difficulty: Difficulty,
    ) -> Obstacle:
        pass

    @abstractmethod
    def generate_difficulty(self, game_state: GameState) -> Difficulty:
        pass

    @abstractmethod
    def evaluate_user_input(
        self,
        user_input: str,
        game_state: GameState,
        location: Location,
        goal: Goal,
        obstacle: Obstacle,
        difficulty: Difficulty,
    ) -> Evaluation:
        pass

    @abstractmethod
    def generate_item(self, game_state: GameState) -> Item:
        pass


class GPTQuestMaster(QuestMaster):
    def generate_item(self, game_state: GameState) -> Item:
        pass

    _gpt_plugin: PluginInstance = PrivateAttr()
    _locations: [
        Location
    ] = PrivateAttr()  # shortcut for loading from game state, etc. for demo purposes
    _obstacles: [
        Obstacle
    ] = PrivateAttr()  # shortcut for loading from game state, etc. for demo purposes

    def __init__(self, client: Steamship):
        self._gpt_plugin = client.use_plugin(
            "gpt-4", config={"model": "gpt-3.5-turbo", "temperature": 0.7}
        )
        self._locations = []
        self._obstacles = []

    def generate_location(self, game_state: GameState) -> Location:
        # chance to generate a progression, etc.

        prior_prompt = ""
        if len(self._locations) > 0:
            location_names = [
                f"{{{loc.name} | {loc.description}}}" for loc in self._locations
            ]
            prior_prompt = f"Prior locations: \n{location_names}."

        prompt = (
            "You are a dungeon master for an online quest game. A player has requested a new quest with the "
            f"following attributes:\nGenre: {game_state.genre}\nTone: {game_state.tone}\n"
            f"The player is on an overall mission to: {game_state.player.motivation}\n "
            f"Please generate a new location for the new quest. The location MUST NOT repeat or be similar to prior locations. "
            f"{prior_prompt}\n"
            f"Locations should be returned in form: {{name | description}}. Location descriptions should "
            f"be no more than one paragraph in length.\n"
            f"Examples:\n"
            f"{{The Misty Mountains Purple | mountains of mystery.}}\n"
            f"{{The Secret Hideout | Dark garage inhibited by henchmen}}.\n"
        )

        task = self._gpt_plugin.generate(text=prompt)
        task.wait()
        out_block = task.output.blocks[0]
        loc_str = out_block.text
        loc_str = loc_str.strip("{}")
        loc_parts = loc_str.split("|")
        name = loc_parts[0].strip("| ")
        desc = loc_parts[1].strip("| ")

        new_loc = Location(name=name, description=desc)
        self._locations.append(new_loc)
        return new_loc

    def generate_quest_goal(self, game_state: GameState, location: Location) -> Goal:
        prompt = (
            "You are a dungeon master for an online quest game. A player has requested a new quest with the "
            f"following attributes:\nGenre: {game_state.genre}\nTone: {game_state.tone}\n"
            f"The player is on an overall mission to: {game_state.player.motivation}\n "
            f"The following location has been chosen for the quest:\n{location.name} - {location.description}\n "
            f"Please generate a goal that the player MUST achieve to complete the quest at that location."
            f"Goals should be returned in form: {{name | description}}. Goal descriptions should "
            f"be no more than one paragraph in length.\n"
            f"Examples:\n"
            f"{{Steal the secret documents | The documents are locked in a safe in the boss's office}}\n"
            f"{{Make friends with a doctor | Befriend Stephanie, the anesthesiologist.}}.\n"
        )

        task = self._gpt_plugin.generate(text=prompt)
        task.wait()
        out_block = task.output.blocks[0]
        goal_str = out_block.text
        goal_str = goal_str.strip("{}")
        goal_parts = goal_str.split("|")
        name = goal_parts[0].strip("| ")
        desc = goal_parts[1].strip("| ")

        return Goal(name=name, description=desc)

    def generate_obstacle(
        self, game_state: GameState, location: Location, goal: Goal
    ) -> Obstacle:
        prior_prompt = ""
        if len(self._locations) > 0:
            obstacles_list = [
                f"{{{o.name} | {o.description}}}" for o in self._obstacles
            ]
            prior_prompt = f"Prior obstacles: \n{obstacles_list}."

        prompt = (
            "You are a dungeon master for an online quest game. A player has requested a new quest with the "
            f"following attributes:\nGenre: {game_state.genre}\nTone: {game_state.tone}\n"
            f"The player is on an overall mission to: {game_state.player.motivation}\n "
            f"The following location has been chosen for the quest:\n{location.name} - {location.description}\n "
            f"The player must achieve the following goal in the quest:\n{goal.name} - {goal.description}\n "
            f"Please generate an obstacle that the player MUST overcome to complete the quest at that location."
            f"The obstacle MUST NOT repeat or be similar to prior obstacles. "
            f"{prior_prompt}\n"
            f"Obstacle should be returned in form: {{name | description}}. Obstacle descriptions should "
            f"be no more than one paragraph in length.\n"
            f"Examples:\n"
            f"{{Security system | The vault is protected by an advanced security system, including cameras and motion detectors.}}\n"
            f"{{Rain | A torrential downpour hits the city, flooding the streets and bringing traffic to a stand-still.}}.\n"
        )

        task = self._gpt_plugin.generate(text=prompt)
        task.wait()
        out_block = task.output.blocks[0]
        obstacle_str = out_block.text
        obstacle_str = obstacle_str.strip("{}")
        obstacle_parts = obstacle_str.split("|")
        name = obstacle_parts[0].strip("| ")
        desc = obstacle_parts[1].strip("| ")

        obstacle = Obstacle(name=name, description=desc)
        self._obstacles.append(obstacle)
        return obstacle

    def generate_difficulty(self, game_state: GameState) -> Difficulty:
        return Difficulty(level=max(len(game_state.quests) * 10, 100))

    def evaluate_user_input(
        self,
        user_input: str,
        game_state: GameState,
        location: Location,
        goal: Goal,
        obstacle: Obstacle,
        difficulty: Difficulty,
    ) -> Evaluation:
        # TODO - add history
        prompt = (
            "You are a dungeon master for an online quest game. "
            f"The game has the following attributes:\nGenre: {game_state.genre}\nTone: {game_state.tone}\n"
            f"The player is currently on a quest to achieve the following goal: {goal.name} - {goal.description}\n "
            f"The quest is happening in the following location:\n{location.name} - {location.description}\n "
            f"The player must overcome the following obstacle:\n{obstacle.name} - {obstacle.description}\n "
            f"The difficulty of the quest is {difficulty.level} out of 100.\n"
            f"Based on the user input, please make an evaluation of the player's progress. The evaluation should be a single"
            f"value selected from the following possible values: [NOT_RELATED, OBSTACLE_NOT_OVERCOME, OBSTACLE_OVERCOME, QUEST_FAILED, QUEST_SUCCEEDED]\n"
            f"OBSTACLE_OVERCOME should only be the evaluation if the user input suggests an outcome with a high likelihood of success.\n"
            f"User Input: {user_input}\n"
            f"Evaluation:"
        )

        task = self._gpt_plugin.generate(text=prompt)
        task.wait()
        out_block = task.output.blocks[0]
        return Evaluation.from_str(out_block.text)


def main():
    with Steamship.temporary_workspace() as client:
        quest_master = GPTQuestMaster(client=client)
        quest_master._locations.append(
            Location(
                name="The Shadowed Streets",
                description="A labyrinth of narrow, dimly lit streets tucked away in the heart of the city. These alleyways are lined with dilapidated buildings, their crumbling facades a reflection of the decaying morals that plague the city. Shadows dance ominously between the flickering streetlights, concealing the secrets and sins that have taken root in this forgotten part of town. The air is heavy with a sense of despair and desperation, as the echoes of whispered deals and illicit activities reverberate through the desolate corridors. It is here, in the heart of the darkness, that the player must navigate the treacherous maze to uncover the truth and bring justice to a city drowning in corruption.",
            )
        )
        quest_master._locations.append(
            Location(
                name="The Crimson Club",
                description="A smoky, dimly lit jazz club nestled in the heart of the city. The air is thick with the scent of whiskey and cigarette smoke, as sultry tunes from a live band fill the room. The patrons, dressed in sharp suits and glamorous gowns, whisper secrets and exchange hushed conversations in the shadows. Behind closed doors, high-stakes poker games and backroom deals take place, fueling the city's corruption. The player must infiltrate this den of vice and unravel the web of deceit that lurks within, exposing the influential figures who pull the strings of power.",
            )
        )
        quest_master._obstacles.append(
            Obstacle(
                name="Broken Floorboards",
                description="As the player enters the abandoned theater, they encounter a section with broken floorboards that span from one end to the other. Precariously balanced, stepping incorrectly on them could cause the player to accidentally trigger a noisy collapse and potentially shatter the element of surprise. Navigating across this obstacle requires careful stepping, dexterity, and soundless movement, as one wrong move could bring unwanted attention to the player's mission.",
            )
        )
        gs = GameState()
        gs.player.motivation = "rid the city of corruption"
        gs.tone = "Dark and gritty"
        gs.genre = "Film noir"
        loc = quest_master.generate_location(game_state=gs)
        print(loc)
        difficulty = quest_master.generate_difficulty(game_state=gs)
        goal = quest_master.generate_quest_goal(gs, loc)
        print(goal)
        obstacle = quest_master.generate_obstacle(gs, loc, goal)
        print(obstacle)
        e = Evaluation.OBSTACLE_NOT_OVERCOME
        while e == Evaluation.OBSTACLE_NOT_OVERCOME:
            user_input = input("What should the player do?")
            e = quest_master.evaluate_user_input(
                user_input=user_input,
                game_state=gs,
                location=loc,
                goal=goal,
                obstacle=obstacle,
                difficulty=difficulty,
            )
            print(e)


if __name__ == "__main__":
    main()
