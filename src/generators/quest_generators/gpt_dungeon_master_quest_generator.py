import random
import time
from typing import Final

from pydantic.fields import PrivateAttr
from steamship import Block, PluginInstance, Steamship, SteamshipError, Tag
from steamship.data.tags import TagKind, TagValueKey
from steamship.data.tags.tag_constants import ChatTag, RoleTag
from steamship.data.block import StreamState
from steamship.agents.schema import AgentContext

from generators import utils
from generators.quest_generator import QuestGenerator
from schema.game_state import GameState
from schema.quest import Quest, QuestLocation, QuestObstacle
from utils.context_utils import get_game_state, with_game_state
from utils.tags import CampTag, QuestIdTag, SceneTag, StoryContextTag, TagKindExtensions

from schema.evaluations import QuestEvaluation, ObstacleEvaluation


class GPTDungeonMasterQuestGenerator(QuestGenerator):
    _gpt: PluginInstance = PrivateAttr()

    def __init__(self, client: Steamship):
        self._gpt = client.use_plugin("gpt-4", config={"model": "gpt-3.5-turbo", "max_tokens": 512})

    def generate_quest_intro(self, context: AgentContext) -> Block:
        game_state = get_game_state(context)
        current_quest_name = game_state.current_quest
        current_quest = next((q for q in game_state.quests if q.name == current_quest_name), None)
        if not current_quest:
            raise SteamshipError("no current quest!")
        completed_quests = [q for q in game_state.quests if q.completed_timestamp]

        past_quests_prompt_component = ""
        if len(completed_quests) > 0:
            past_quests_prompt_component = f"{game_state.player.name} has completed the following quests: \n"
            for cq in completed_quests:
                past_quests_prompt_component += f"- {cq.name}: {cq.text_summary}\n"

        current_quest_prompt_component = f"{game_state.player.name} is now on a quest at " \
                                         f"{current_quest.location.name}. " \
                                         f"The goal of this quest is {current_quest.goal}.\n" \
                                         f"Tell the story of the beginning of the quest in two paragraphs."

        full_prompt = f"{past_quests_prompt_component}{current_quest_prompt_component}"

        block = context.chat_history.append_system_message(
            text=full_prompt,
            tags=[Tag(kind="quest-generation", name="intro-prompt")]
        )

        block_indices = [game_state.system_prompt_index_in_file, block.index_in_file]

        task = self._gpt.generate(input_file_id=context.chat_history.file.id, input_file_block_index_list=block_indices,
                                  append_output_to_file=True, streaming=True,
                                  output_file_id=context.chat_history.file.id, make_output_public=True,
                                  tags=[Tag(kind=TagKind.CHAT, name=ChatTag.ROLE, value={TagValueKey.STRING_VALUE: RoleTag.ASSISTANT})])
        task.wait()
        return task.output.blocks[0]

    def create_quest_obstacle(self, context: AgentContext) -> QuestObstacle:
        game_state = get_game_state(context)
        current_quest_name = game_state.current_quest
        current_quest = next((q for q in game_state.quests if q.name == current_quest_name), None)
        if not current_quest:
            raise SteamshipError("no current quest!")
        past_obstacles = []
        for q in game_state.quests:
            past_obstacles.extend(q.obstacles)

        past_obstacles_prompt = ""
        if len(past_obstacles) > 0:
            past_obstacles_prompt = f"{game_state.player.name} has faced the previous obstacles: \n"
            for o in past_obstacles:
                past_obstacles_prompt += f"- {o.obstacle_type}: {o.obstacle_description}\n"

        obstacle_prompt = f"""Generate a challenge or obstacle that must be overcome by {game_state.player.name} on their quest to {current_quest.goal}. The obstacle should fit in within the overall quest location of {current_quest.location.name}.
        
The situation or obstacle should not be repeate prior obstacles or challenges faced by {game_state.player.name} in other quests. {past_obstacles_prompt}.

The obstacle must also not repeat the overall goal of the quest ({current_quest.goal}).
        
Obstacle should be returned in form: {{type | description}}. Obstacle descriptions should be no more than one paragraph in length.

Examples:
{{ Keypad Lock | A keypad protects access to the locked freezer at the restaurant, preventing access to the secret ingredients }}
{{ Corrupt Politician | A corrupt city official is blocking all attempts to get the proper approvals for new construction }} 
"""

        block = context.chat_history.append_system_message(
            text=obstacle_prompt,
            tags=[Tag(kind="quest-generation", name="obstacle-generation")]
        )

        block_indices = [game_state.system_prompt_index_in_file, block.index_in_file]

        # not streaming, not saved to chat history
        task = self._gpt.generate(input_file_id=context.chat_history.file.id, input_file_block_index_list=block_indices)
        task.wait()
        obstacle_text = task.output.blocks[0].text
        obstacle_str = obstacle_text.strip("{}")
        obstacle_parts = obstacle_str.split("|")
        ob_type = obstacle_parts[0].strip("| ")
        desc = obstacle_parts[1].strip("| ")

        obstacle = QuestObstacle(obstacle_type=ob_type, obstacle_description=desc)
        return obstacle

    def generate_obstacle_text(self, context: AgentContext):
        game_state = get_game_state(context)
        current_quest_name = game_state.current_quest
        current_quest = next((q for q in game_state.quests if q.name == current_quest_name), None)
        if not current_quest:
            raise SteamshipError("no current quest!")

        num_paragraphs = random.randint(1, 2)
        prompt = f"""Generate {num_paragraphs} short paragraphs that present {game_state.player.name} with
the following challenge on their current quest: {current_quest.obstacles[-1].obstacle_type} -- 
{current_quest.obstacles[-1].obstacle_description}. 

DO NOT SOLVE the challenge for {game_state.player.name}. The generated text should allow {game_state.player.name} to
decide how to attempt to solve the challenge. The challenge can require {game_state.player.name} to string
together multiple actions. 
"""

        block = context.chat_history.append_system_message(
            text=prompt,
            tags=[Tag(kind="quest-generation", name="obstacle-text-prompt")]
        )

        block_indices = [game_state.system_prompt_index_in_file, current_quest.intro_block_index_in_file, block.index_in_file]
        task = self._gpt.generate(input_file_id=context.chat_history.file.id, input_file_block_index_list=block_indices,
                                  append_output_to_file=True, streaming=True,
                                  output_file_id=context.chat_history.file.id, make_output_public=True,
                                  tags=[Tag(kind=TagKind.CHAT, name=ChatTag.ROLE,
                                            value={TagValueKey.STRING_VALUE: RoleTag.ASSISTANT})])
        task.wait()
        return task.output.blocks[0]

    def evaluate_user_input_for_obstacle(self, user_input: str, context: AgentContext) -> ObstacleEvaluation:
        game_state = get_game_state(context)
        current_quest_name = game_state.current_quest
        current_quest = next((q for q in game_state.quests if q.name == current_quest_name), None)
        if not current_quest:
            raise SteamshipError("no current quest!")

        obstacle = current_quest.obstacles[-1]
        # prompt =f"{game_state.player.name} is currently on a quest to achieve the following goal: {current_quest.goal}\n "
        # f"The quest is happening in the following location:\n{current_quest.location.name} - {current_quest.location.description}\n "
        # f"The player must overcome the following obstacle:\n{obstacle.obstacle_type} - {obstacle.obstacle_description}\n "
        prompt = f"Evaluate {game_state.player.name}'s progress related to the current obstabcle. " \
                 f"The evaluation should be a single value selected from the following possible values: " \
                 f"[NOT_RELEVANT, OBSTACLE_NOT_OVERCOME, OBSTACLE_OVERCOME]\n" \
                 f"OBSTACLE_OVERCOME should only be the evaluation if the user input suggests an outcome with a" \
                 f" high likelihood of success.\n"

        # TODO: tag this for filtering?
        prompt_block = context.chat_history.append_system_message(text=prompt)

        block_indices = [current_quest.intro_block_index_in_file]

        # TODO: do some sort of token minimization where we only use the last N blocks to control prompt
        # size explosion or do we want some sort of summarization ?
        block_indices.extend(current_quest.obstacles[-1].block_indices)
        block_indices.append(prompt_block.index_in_file)

        # not streaming, does not need to be in chat history
        task = self._gpt.generate(input_file_id=context.chat_history.file.id, input_file_block_index_list=block_indices,
                                  tags=[Tag(kind="quest-generation", name="obstacle-evaluation-prompt")])
        task.wait()
        eval_text = task.output.blocks[0].text
        return ObstacleEvaluation.from_str(eval_text)

    def generate_obstacle_failed_text(self, user_input: str, context: AgentContext):
        game_state = get_game_state(context)
        current_quest_name = game_state.current_quest
        current_quest = next((q for q in game_state.quests if q.name == current_quest_name), None)
        if not current_quest:
            raise SteamshipError("no current quest!")

        num_paragraphs = random.randint(1, 2)
        prompt = f"""Generate {num_paragraphs} short paragraphs that tell the story of {game_state.player.name} attempting
        to overcome the existing obstabcle, but failing. The generated text should allow {game_state.player.name} to
        decide how to continued attempt to solve the challenge.
        """

        block = context.chat_history.append_system_message(
            text=prompt,
            tags=[Tag(kind="quest-generation", name="obstacle-text-prompt-fail")]
        )

        block_indices = [game_state.system_prompt_index_in_file, current_quest.intro_block_index_in_file]
        block_indices.extend(current_quest.obstacles[-1].block_indices)
        block_indices.append(block.index_in_file)
        task = self._gpt.generate(input_file_id=context.chat_history.file.id, input_file_block_index_list=block_indices,
                                  append_output_to_file=True, streaming=True,
                                  output_file_id=context.chat_history.file.id, make_output_public=True,
                                  tags=[Tag(kind=TagKind.CHAT, name=ChatTag.ROLE,
                                            value={TagValueKey.STRING_VALUE: RoleTag.ASSISTANT})])
        task.wait()
        return task.output.blocks[0]

    def generate_obstacle_passed_text(self, user_input: str, context: AgentContext):
        game_state = get_game_state(context)
        current_quest_name = game_state.current_quest
        current_quest = next((q for q in game_state.quests if q.name == current_quest_name), None)
        if not current_quest:
            raise SteamshipError("no current quest!")

        num_paragraphs = random.randint(1, 2)
        prompt = f"""Generate {num_paragraphs} short paragraphs that tell the story of {game_state.player.name} 
               overcoming the existing obstabcle. The generated text should allow {game_state.player.name} to
               continue on their quest to {current_quest.goal}.
               """

        block = context.chat_history.append_system_message(
            text=prompt,
            tags=[Tag(kind="quest-generation", name="obstacle-text-prompt-fail")]
        )

        block_indices = [game_state.system_prompt_index_in_file, current_quest.intro_block_index_in_file]
        block_indices.extend(current_quest.obstacles[-1].block_indices)
        block_indices.append(block.index_in_file)
        task = self._gpt.generate(input_file_id=context.chat_history.file.id, input_file_block_index_list=block_indices,
                                  append_output_to_file=True, streaming=True,
                                  output_file_id=context.chat_history.file.id, make_output_public=True,
                                  tags=[Tag(kind=TagKind.CHAT, name=ChatTag.ROLE,
                                            value={TagValueKey.STRING_VALUE: RoleTag.ASSISTANT})])
        task.wait()
        return task.output.blocks[0]

    def evaluate_user_input_for_quest(self, user_input: str, context: AgentContext) -> QuestEvaluation:
        pass

    def generate_quest_incomplete_text(self, user_input: str, context: AgentContext):
        pass

    def generate_quest_complete_text(self, user_input: str, context: AgentContext):
        pass

    def generate_item_for_quest(self, context: AgentContext):
        pass


GAME_PROMPT = """You are a dungeon master for an online quest game. In this game, players go on multiple quests in
order to achieve an overall goal. Completing quests represents building progress towards that overall goal. Quests
take place in location, involve obstacles that must be overcome throughout the quest, and end with the player
having either found an item that will help them in subsequent quests, or having achieved their ultimate goal. 

A player has requested a new game with the following attributes: 
Genre: Mystery
Tone: Upbeat and Funny

The player is playing as a character named Mr. Meatball.

Mr. Meatball has the following background: Born on a plate of spaghetti. Loves parmesan cheese and tomato sauce.
Mr. Meatball's overall goal is to: become the world's best chef.

Each quest that Mr. Meatball goes on MUST further them towards that overall goal.
"""


def main():
    gs = GameState()
    gs.player.name = "Mr. Meatball"
    gs.quests = [
        Quest(name="Pass The Cheese",
              description="Parmesan cheese has gone missing. And dinner is in 1 hour!",
              goal="Mr. Meatball must find the missing parmesan cheese in order to make dinner"
                          " for all his friends",
              location=QuestLocation(
                  name="Papa Joe's Restaurant",
                  description="A hole-in-the-wall italian joint that serves endless plates of pasta and marinara."
              ),
              obstacles=[
                  QuestObstacle(obstacle_type='Missing Recipe Book',
                                obstacle_description="The recipe book containing the secret to Papa Joe's famous "
                                                     "tomato sauce has gone missing, and without it, Mr. Meatball "
                                                     "won't be able to recreate the sauce for his friends."
                                ),
              ]
              ),
    ]

    with Steamship.temporary_workspace() as client:
        context = AgentContext.get_or_create(
            client=client,
            context_keys={"id": f"foo-testing"},
            use_llm_cache=False,
            use_action_cache=False,
            initial_system_message="",  # None necessary
            searchable=False,
        )
        block = context.chat_history.append_system_message(text=GAME_PROMPT)
        gs.system_prompt_index_in_file = block.index_in_file
        gs.current_quest = "Pass The Cheese"
        context = with_game_state(context=context, game_state=gs)

        dungeon_master = GPTDungeonMasterQuestGenerator(client=client)

        block = dungeon_master.generate_quest_intro(context=context)
        while block.stream_state in [StreamState.STARTED]:
            time.sleep(0.1)
            block = Block.get(client, _id=block.id)

        print(block.text)
        gs.quests[0].intro_block_index_in_file = block.index_in_file

        obstacle = dungeon_master.create_quest_obstacle(context=context)
        print(f"\n [ OBSTACLE ] {obstacle}\n")
        gs.quests[0].obstacles.append(obstacle)

        block = dungeon_master.generate_obstacle_text(context=context)
        while block.stream_state in [StreamState.STARTED]:
            time.sleep(0.1)
            block = Block.get(client, _id=block.id)

        print(block.text, "\n")
        obstacle.block_indices.append(block.index_in_file)

        user_next = input("What does he do next?\n")
        user_block = context.chat_history.append_user_message(text=user_next, tags=[Tag(kind=TagKind.CHAT,
                                                                                        name=ChatTag.ROLE,
                                                                                        value={
                                                                                            TagValueKey.STRING_VALUE:
                                                                                                RoleTag.USER})]
                                                              )
        obstacle.block_indices.append(user_block.index_in_file)
        evaluation = dungeon_master.evaluate_user_input_for_obstacle(user_input=user_next, context=context)

        print(f"\n [ EVALUATION ] - {evaluation.name} ")

        while evaluation not in [ObstacleEvaluation.OBSTACLE_OVERCOME]:
            block = dungeon_master.generate_obstacle_failed_text(user_input=user_next, context=context)
            while block.stream_state in [StreamState.STARTED]:
                time.sleep(0.1)
                block = Block.get(client, _id=block.id)

            print(block.text, "\n")
            obstacle.block_indices.append(block.index_in_file)

            user_next = input("What does he do next?\n")
            user_block = context.chat_history.append_user_message(text=user_next,
                                                                  tags=[Tag(kind=TagKind.CHAT, name=ChatTag.ROLE,
                                                                            value={
                                                                                TagValueKey.STRING_VALUE: RoleTag.USER})]
                                                                  )
            obstacle.block_indices.append(user_block.index_in_file)
            evaluation = dungeon_master.evaluate_user_input_for_obstacle(user_input=user_next, context=context)
            print(f"\n [ EVALUATION ] - {evaluation.name} ")

        block = dungeon_master.generate_obstacle_passed_text(user_input=user_next, context=context)
        while block.stream_state in [StreamState.STARTED]:
            time.sleep(0.1)
            block = Block.get(client, _id=block.id)

        print(block.text, "\n")
        obstacle.block_indices.append(block.index_in_file)


if __name__ == "__main__":
    main()
