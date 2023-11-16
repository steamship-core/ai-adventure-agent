import time
from typing import List

from pydantic_yaml import parse_yaml_raw_as
from steamship import Block, Steamship, Workspace
from steamship.agents.schema import AgentContext
from steamship.data import TagKind
from steamship.data.block import StreamState
from steamship.data.tags.tag_constants import RoleTag

from api import AdventureGameService
from generators.generator_context_utils import set_image_generator, set_music_generator
from schema.characters import HumanCharacter
from schema.game_state import ActiveMode
from schema.server_settings import ServerSettings
from utils.context_utils import (
    get_game_state,
    get_story_text_generator,
    save_game_state,
    save_server_settings,
)
from utils.dummy_generator import DummyGenerator
from utils.tags import QuestArcTag, QuestTag, TagKindExtensions

output_tags = [
    (TagKindExtensions.QUEST_ARC, QuestArcTag.RESULT),
    (TagKindExtensions.QUEST, QuestTag.QUEST_CONTENT),
    (TagKindExtensions.QUEST, QuestTag.DICE_ROLL),
]


class AutoPlayHarness:
    server_settings: ServerSettings
    character: HumanCharacter
    workspace: Workspace
    client: Steamship
    service: AdventureGameService
    last_seen_block = -1
    last_content_block: Block
    context: AgentContext

    def __init__(self, server_settings_path: str, character_path: str):
        with open(server_settings_path) as settings_file:
            yaml_string = settings_file.read()
            self.server_settings = parse_yaml_raw_as(ServerSettings, yaml_string)

        with open(character_path) as character_file:
            yaml_string = character_file.read()
            self.character = parse_yaml_raw_as(HumanCharacter, yaml_string)

        self.client = Steamship()
        self.workspace = Workspace.create(self.client)
        self.client.switch_workspace(workspace_id=self.workspace.id)

        self.service = AdventureGameService(client=self.client)

        self.context = self.service.build_default_context()
        save_server_settings(self.server_settings, self.context)
        game_state = get_game_state(self.context)
        game_state.player = self.character
        save_game_state(game_state, self.context)

        # Override image and music generators
        dummy_generator = DummyGenerator(self.client)
        set_image_generator(self.context, dummy_generator)
        set_music_generator(self.context, dummy_generator)

    def print_object_or_objects(self, output: List[Block]):
        context = AgentContext.get_or_create(
            client=self.client,
            context_keys={"id": "default"},
            searchable=False,
        )
        for block in context.chat_history.file.blocks:
            if block.index_in_file > self.last_seen_block:
                if block.stream_state == StreamState.STARTED:
                    start_time = time.perf_counter()
                    while (
                        block.stream_state
                        not in [
                            StreamState.COMPLETE,
                            StreamState.ABORTED,
                        ]
                        and (time.perf_counter() - start_time) < 30
                    ):
                        time.sleep(0.4)
                        block = Block.get(block.client, _id=block.id)
                for tag in block.tags:
                    if (
                        tag.kind == TagKindExtensions.QUEST
                        and tag.name == QuestTag.QUEST_CONTENT
                    ):
                        self.last_content_block = block

                self.print_new_block(block)
        self.last_seen_block = context.chat_history.file.blocks[-1].index_in_file
        print(f"LAST SEEN BLOCK: {self.last_seen_block}")
        # for object in output:
        #     self.print_new_block(object)

    def print_new_block(self, block: Block):
        tag_kinds = {tag.kind for tag in block.tags}
        # tag_names = {tag.name for tag in block.tags}
        if (
            TagKind.STATUS_MESSAGE not in tag_kinds
            and TagKindExtensions.INSTRUCTIONS not in tag_kinds
            and block.chat_role not in [RoleTag.USER]
        ):
            tag_texts = "".join(
                sorted({f"[{tag.kind},{tag.name}]" for tag in block.tags})
            )
            if block.is_text():
                print(f"[{block.index_in_file}] {tag_texts} {block.text}\n")
            else:
                print(f"[{block.index_in_file}] {tag_texts} {block.raw_data_url}")

    def prompt(self, prompt: str):
        self.print_object_or_objects(self.service.prompt(prompt=prompt))

    def run_quest(self):
        self.prompt("go")
        self.prompt("go on a quest")
        while get_game_state(self.context).active_mode == ActiveMode.QUEST:
            print(f"LAST CONTENT BLOCK: {self.last_content_block.text}")
            suggestion = self.suggest_solution(self.last_content_block.text)
            self.prompt(suggestion)

    def suggest_solution(self, problem_text: str) -> str:
        generator = get_story_text_generator(self.context)
        suggestion = (
            generator.generate(
                text=problem_text + " In one quick sentence, what should they do? "
            )
            .wait()
            .blocks[0]
            .text
        )
        print(f"SUGGESTION: {suggestion}")
        return suggestion


if __name__ == "__main__":
    harness = AutoPlayHarness(
        "example_content/evil_science_server_settings.yaml",
        "example_content/evil_science_character.yaml",
    )
    harness.run_quest()
