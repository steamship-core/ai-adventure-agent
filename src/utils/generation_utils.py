"""
Like context_utils, this is meant to provide a light-weight set of utilities.

The goal is to enable the game designer work in a high signal-to-noise environment, like this:

    send_background_music("description", context)
    send_assistant_message("Hi there!", context)

While at the same time not committing to any huge abstraction overhead: this is just a light-weight set of helper
functions whose mechanics can change under the hood as we discover better ways to do things, and the game developer
doesn't need to know.
"""
import logging
import time
from typing import List, Optional, Tuple

from steamship import Block, Tag
from steamship.agents.schema import AgentContext
from steamship.agents.schema.message_selectors import tokens
from steamship.data import TagKind
from steamship.data.block import StreamState
from steamship.data.tags.tag_constants import ChatTag, RoleTag, TagValueKey

from schema.characters import HumanCharacter
from schema.quest import QuestDescription
from utils.ChatHistoryFilter import (
    ChatHistoryFilter,
    LastInventoryFilter,
    QuestNameFilter,
    TagFilter,
    TrimmingStoryContextFilter,
    UnionFilter,
)
from utils.context_utils import (
    emit,
    get_game_state,
    get_server_settings,
    get_story_text_generator,
)
from utils.tags import (
    AgentStatusMessageTag,
    CharacterTag,
    MerchantTag,
    QuestArcTag,
    QuestIdTag,
    QuestTag,
    StoryContextTag,
    TagKindExtensions,
)


def send_agent_status_message(
    name: AgentStatusMessageTag, context: AgentContext, value: Optional[dict] = None
) -> Optional[Block]:
    block = Block(
        text="",
        tags=[
            Tag(kind=TagKind.ROLE, name="status-message", value=value),
            Tag(kind=TagKind.AGENT_STATUS_MESSAGE, name=name.value, value=value),
        ],
    )
    emit(block, context=context)
    return block


def send_story_generation(
    prompt: str, quest_name: str, context: AgentContext
) -> Optional[Block]:
    """Generates and sends a background image to the player."""
    block = do_token_trimmed_generation(
        context,
        prompt,
        prompt_tags=[
            Tag(kind=TagKindExtensions.QUEST, name=QuestTag.QUEST_PROMPT),
            QuestIdTag(quest_name),
        ],
        output_tags=[
            Tag(kind=TagKindExtensions.QUEST, name=QuestTag.QUEST_CONTENT),
            QuestIdTag(quest_name),
        ],
        filter=UnionFilter(
            [
                TagFilter(
                    tag_types=[
                        (TagKindExtensions.CHARACTER, CharacterTag.NAME),
                        (TagKindExtensions.CHARACTER, CharacterTag.MOTIVATION),
                        (TagKindExtensions.CHARACTER, CharacterTag.DESCRIPTION),
                        (TagKindExtensions.CHARACTER, CharacterTag.BACKGROUND),
                        (TagKindExtensions.STORY_CONTEXT, StoryContextTag.TONE),
                        (TagKindExtensions.STORY_CONTEXT, StoryContextTag.BACKGROUND),
                        (TagKindExtensions.STORY_CONTEXT, StoryContextTag.VOICE),
                        (TagKindExtensions.QUEST, QuestTag.QUEST_SUMMARY),
                    ]
                ),
                QuestNameFilter(quest_name=quest_name),
                LastInventoryFilter(),
            ]
        ),
        generation_for="Quest Content",
        # stop_tokens=["\n"],
    )
    return block


def generate_likelihood_estimation(
    prompt: str, quest_name: str, context: AgentContext
) -> Optional[Block]:
    """Generates a likelihood calculation of success for an event."""
    block = do_token_trimmed_generation(
        context,
        prompt,
        prompt_tags=[
            Tag(kind=TagKindExtensions.QUEST, name=QuestTag.LIKELIHOOD_EVALUATION),
            QuestIdTag(quest_name),
        ],
        output_tags=[],
        filter=UnionFilter(
            [
                TagFilter(
                    tag_types=[
                        (TagKindExtensions.CHARACTER, CharacterTag.NAME),
                        (TagKindExtensions.CHARACTER, CharacterTag.MOTIVATION),
                        (TagKindExtensions.CHARACTER, CharacterTag.DESCRIPTION),
                        (TagKindExtensions.CHARACTER, CharacterTag.BACKGROUND),
                        (TagKindExtensions.STORY_CONTEXT, StoryContextTag.TONE),
                        (TagKindExtensions.STORY_CONTEXT, StoryContextTag.BACKGROUND),
                        (TagKindExtensions.QUEST, QuestTag.QUEST_SUMMARY),
                    ]
                ),
                QuestNameFilter(quest_name=quest_name),
                LastInventoryFilter(),
            ]
        ),
        generation_for="Dice Roll",
        stop_tokens=["\n"],
        new_file=True,
        streaming=False,
    )
    return block


def generate_quest_summary(quest_name: str, context: AgentContext) -> Optional[Block]:
    """Generates and sends a quest summary to the player."""
    prompt = "Please summarize the above quest in one to two sentences."
    block = do_token_trimmed_generation(
        context,
        prompt,
        prompt_tags=[
            Tag(kind=TagKindExtensions.QUEST, name=QuestTag.QUEST_PROMPT),
            QuestIdTag(quest_name),
        ],
        output_tags=[
            Tag(kind=TagKindExtensions.QUEST, name=QuestTag.QUEST_SUMMARY),
            QuestIdTag(quest_name),
        ],
        filter=QuestNameFilter(quest_name=quest_name),
        generation_for="Quest Summary",
        # stop_tokens=["\n"],
    )
    return block


def generate_quest_item(
    quest_name: str, player: HumanCharacter, context: AgentContext
) -> (str, str):
    """Generates a found item from a quest, returning a tuple of its name and description"""
    prompt = f"What item did {player.name} find during that story? It should fit the setting of the story and help {player.name} achieve their goal. Please respond only with ITEM NAME: <name> ITEM DESCRIPTION: <description>"
    block = do_token_trimmed_generation(
        context,
        prompt,
        prompt_tags=[
            Tag(kind=TagKindExtensions.QUEST, name=QuestTag.ITEM_GENERATION_PROMPT),
            QuestIdTag(quest_name),
        ],
        output_tags=[
            Tag(kind=TagKindExtensions.QUEST, name=QuestTag.ITEM_GENERATION_CONTENT),
            QuestIdTag(quest_name),
        ],
        filter=UnionFilter(
            [QuestNameFilter(quest_name=quest_name), LastInventoryFilter()]
        ),
        generation_for="Quest Item",
        streaming=False,
    )
    parts = block.text.split("ITEM DESCRIPTION:")
    if len(parts) == 2:
        name = parts[0].replace("ITEM NAME:", "").strip()
        description = parts[1].strip()
    else:
        name = block.text.strip()
        description = ""
    return name, description


def generate_merchant_inventory(
    player: HumanCharacter, context: AgentContext
) -> List[Tuple[str, str]]:
    """Generates the inventory for a merchant"""
    prompt = f"Please list 5 objects that a merchant might sell {player.name} in a shop. They should fit the setting of the story and help {player.name} achieve their goal. Please respond only with ITEM NAME: <name> ITEM DESCRIPTION: <description>"
    block = do_generation(
        context,
        prompt,
        prompt_tags=[
            Tag(
                kind=TagKindExtensions.MERCHANT,
                name=MerchantTag.INVENTORY_GENERATION_PROMPT,
            )
        ],
        output_tags=[Tag(kind=TagKindExtensions.MERCHANT, name=MerchantTag.INVENTORY)],
        filter=UnionFilter(
            [
                TagFilter(
                    [
                        (TagKindExtensions.CHARACTER, CharacterTag.NAME),
                        (TagKindExtensions.CHARACTER, CharacterTag.MOTIVATION),
                        (TagKindExtensions.CHARACTER, CharacterTag.DESCRIPTION),
                        (TagKindExtensions.CHARACTER, CharacterTag.BACKGROUND),
                        (TagKindExtensions.STORY_CONTEXT, StoryContextTag.TONE),
                        (TagKindExtensions.STORY_CONTEXT, StoryContextTag.BACKGROUND),
                        (TagKindExtensions.QUEST, QuestTag.QUEST_SUMMARY),
                        (
                            TagKindExtensions.MERCHANT,
                            MerchantTag.INVENTORY_GENERATION_PROMPT,
                        ),
                    ]
                ),
                LastInventoryFilter(),
            ]
        ),
        generation_for="Merchant Inventory",
        streaming=False,
    )
    result = []
    items = block.text.split("ITEM NAME:")
    for item in items:
        if len(item.strip()) > 0:
            parts = item.split("ITEM DESCRIPTION:")
            if len(parts) == 2:
                name = parts[0].replace("ITEM NAME:", "").strip()
                description = parts[1].strip()
            else:
                name = item.strip()
                description = ""
            result.append((name, description))
    return result


def generate_quest_arc(
    player: HumanCharacter, context: AgentContext
) -> List[QuestDescription]:
    server_settings = get_server_settings(context)
    prompt = (
        f"Please list {server_settings.quests_per_arc} quests of increasing difficulty that {player.name} will go in to achieve their overall "
        f"goal of {server_settings.adventure_goal}. They should fit the setting of the story. Responses should only be in the "
        f"form of: QUEST GOAL: <goal> QUEST LOCATION: <location name>\n"
        f"Example (for a quest game for a dog):\n"
        f"QUEST GOAL: find a treat QUEST LOCATION: Dog Park\n"
        f"QUEST GOAL: make a friend QUEST LOCATION: Main Street\n"
        f"QUEST GOAL: get bacon from the butcher QUEST LOCATION: Butcher Shop\n"
        f"QUEST GOAL: learn a new trick QUEST LOCATION: Trainer's Office\n"
        f"QUEST GOAL: fetch the newspaper QUEST LOCATION: Owner's House\n"
        f"QUEST GOAL: prevent a robbery QUEST LOCATION: Owner's Store\n"
        f"QUEST GOAL: impress the teacher during a show and tell QUEST LOCATION: Owner's Kid's School\n"
        f"QUEST GOAL: steal some turkey QUEST LOCATION: Thanksgiving Dinner at Grandma's\n"
        f"QUEST GOAL: get your nails trimmed QUEST LOCATION: Dog Wash\n"
        f"QUEST GOAL: win an award QUEST LOCATION: Westminister Dog Show\n"
    )
    result: List[QuestDescription] = []
    while len(result) != server_settings.quests_per_arc:
        block = do_generation(
            context,
            prompt,
            prompt_tags=[
                Tag(
                    kind=TagKindExtensions.QUEST_ARC,
                    name=QuestArcTag.PROMPT,
                )
            ],
            output_tags=[
                Tag(kind=TagKindExtensions.QUEST_ARC, name=QuestArcTag.RESULT)
            ],
            filter=TagFilter(
                [
                    (TagKindExtensions.CHARACTER, CharacterTag.NAME),
                    (TagKindExtensions.CHARACTER, CharacterTag.DESCRIPTION),
                    (TagKindExtensions.CHARACTER, CharacterTag.BACKGROUND),
                    (TagKindExtensions.STORY_CONTEXT, StoryContextTag.TONE),
                    (TagKindExtensions.STORY_CONTEXT, StoryContextTag.BACKGROUND),
                    (TagKindExtensions.QUEST_ARC, QuestArcTag.PROMPT),
                ]
            ),
            generation_for="Quest Arc",
            streaming=False,
        )
        result = []
        items = block.text.split("QUEST GOAL:")
        for item in items:
            if len(item.strip()) > 0 and "QUEST LOCATION" in item:
                parts = item.split("QUEST LOCATION:")
                if len(parts) == 2:
                    goal = parts[0].strip()
                    location = parts[1].strip().rstrip(".")
                    if "\n" in location:
                        location = location[: location.index("\n")]
                    result.append(QuestDescription(goal=goal, location=location))
    return result


def generate_story_intro(player: HumanCharacter, context: AgentContext) -> str:
    server_settings = get_server_settings(context)
    prompt = f"Please write a few sentences of introduction to the character {player.name} as they embark on their journey to {server_settings.adventure_goal}."
    block = do_token_trimmed_generation(
        context,
        prompt,
        prompt_tags=[
            Tag(
                kind=TagKindExtensions.CHARACTER,
                name=CharacterTag.INTRODUCTION_PROMPT,
            )
        ],
        output_tags=[
            Tag(kind=TagKindExtensions.CHARACTER, name=CharacterTag.INTRODUCTION)
        ],
        filter=TagFilter(
            [
                (TagKindExtensions.CHARACTER, CharacterTag.NAME),
                (TagKindExtensions.CHARACTER, CharacterTag.DESCRIPTION),
                (TagKindExtensions.CHARACTER, CharacterTag.BACKGROUND),
                (TagKindExtensions.STORY_CONTEXT, StoryContextTag.TONE),
                (TagKindExtensions.STORY_CONTEXT, StoryContextTag.BACKGROUND),
                (TagKindExtensions.STORY_CONTEXT, StoryContextTag.VOICE),
                (TagKindExtensions.CHARACTER, CharacterTag.INTRODUCTION_PROMPT),
            ]
        ),
        generation_for="Character Introduction",
        streaming=False,
    )
    return block.text


def do_token_trimmed_generation(
    context: AgentContext,
    prompt: str,
    prompt_tags: List[Tag],
    output_tags: List[Tag],
    filter: ChatHistoryFilter,
    generation_for: str,  # For debugging output
    stop_tokens: Optional[List[str]] = None,
    new_file: bool = False,
    streaming: bool = True,
) -> Block:
    game_state = get_game_state(context=context)
    server_settings = get_server_settings(context)
    avail_tokens = 4096 - server_settings.default_story_max_tokens
    avail_tokens -= tokens(Block(text=prompt))

    block = do_generation(
        context,
        prompt,
        prompt_tags=prompt_tags,
        output_tags=output_tags,
        filter=TrimmingStoryContextFilter(
            base_filter=filter,
            current_quest_id=game_state.current_quest,
            game_state=game_state,
            max_tokens=avail_tokens,
        ),
        generation_for=generation_for,
        stop_tokens=stop_tokens,
        new_file=new_file,
        streaming=streaming,
    )
    return block


def do_generation(
    context: AgentContext,
    prompt: str,
    prompt_tags: List[Tag],
    output_tags: List[Tag],
    filter: ChatHistoryFilter,
    generation_for: str,  # For debugging output
    stop_tokens: Optional[List[str]] = None,
    new_file: bool = False,
    streaming: bool = True,
) -> Block:
    """Generates the inventory for a merchant"""

    generator = get_story_text_generator(context)

    output_tags.extend(
        [
            Tag(
                kind=TagKind.CHAT,
                name=ChatTag.ROLE,
                value={TagValueKey.STRING_VALUE: RoleTag.ASSISTANT},
            ),
            Tag(kind=TagKind.CHAT, name=ChatTag.MESSAGE),
            # See agent_service.py::chat_history_append_func for the duplication prevention this tag results in
            Tag(kind=TagKind.CHAT, name="streamed-to-chat-history"),
        ]
    )

    prompt_block = context.chat_history.append_system_message(
        text=prompt,
        tags=prompt_tags,
    )
    # Intentionally reuse the filtering for the quest CONTENT
    block_indices = filter.filter_chat_history(
        chat_history_file=context.chat_history.file, filter_for=generation_for
    )

    if prompt_block.index_in_file not in block_indices:
        block_indices.append(prompt_block.index_in_file)

    options = {}
    if stop_tokens:
        options["stop"] = stop_tokens

    output_file_id = None if new_file else context.chat_history.file.id

    # don't pollute workspace with temporary/working files that contain data like: "LIKELY"
    append_output_to_file = False if not output_file_id else True

    logging.debug(
        f"current prompt({prompt_block.index_in_file}, {tokens(prompt_block)}): {prompt}"
    )
    logging.debug(f"selected blocks: {sorted(block_indices)}")

    task = generator.generate(
        tags=output_tags,
        append_output_to_file=append_output_to_file,
        input_file_id=context.chat_history.file.id,
        output_file_id=output_file_id,
        streaming=streaming,
        input_file_block_index_list=sorted(block_indices),
        options=options,
    )
    task.wait()
    blocks = task.output.blocks
    block = blocks[0]
    # only re-fetch block if it is not ephemeral...
    if block.client and block.id:
        block = Block.get(block.client, _id=block.id)
    emit(output=block, context=context)  # todo: should emit be optional ?
    return block


def await_streamed_block(block: Block, context: AgentContext) -> Block:
    while block.stream_state not in [StreamState.COMPLETE, StreamState.ABORTED]:
        time.sleep(0.4)
        block = Block.get(block.client, _id=block.id)
    context.chat_history.file.refresh()
    return block


def generate_action_choices(context: AgentContext) -> Block:

    game_state = get_game_state(context)
    quest_name = game_state.current_quest

    prompt = (
        f"Generate a multiple choice set of four options for the user to select {game_state.player.name}'s next "
        f'action. The actions should be relevant to the story and include a single "custom" option that '
        f"allows the user to provide their own action in the story. "
        "The generated actions should match the tone and narrative voice of the existing story.\n"
        "Action choices should be returned as a JSON map that provides a single letter key for each action "
        "choice, as follows: \n"
        '{"A": "pet the dog", "B": "launch missiles", "C": "dance the macarana", "D": "custom" }'
    )

    block = do_token_trimmed_generation(
        context,
        prompt,
        prompt_tags=[
            # intentionally don't add this to the quest. it lives as sorta "out-of-quest" generation
            # that still requires quest data.
            Tag(kind=TagKindExtensions.QUEST, name=QuestTag.ACTION_CHOICES_PROMPT),
        ],
        output_tags=[
            # provide a way to filter this out, in case this ends up in a saved file somewhere (not currently)
            Tag(kind=TagKindExtensions.QUEST, name=QuestTag.ACTION_CHOICES),
        ],
        filter=UnionFilter(
            [
                TagFilter(
                    tag_types=[
                        (TagKindExtensions.CHARACTER, CharacterTag.NAME),
                        (TagKindExtensions.CHARACTER, CharacterTag.MOTIVATION),
                        (TagKindExtensions.CHARACTER, CharacterTag.DESCRIPTION),
                        (TagKindExtensions.CHARACTER, CharacterTag.BACKGROUND),
                        (TagKindExtensions.STORY_CONTEXT, StoryContextTag.TONE),
                        (TagKindExtensions.STORY_CONTEXT, StoryContextTag.BACKGROUND),
                        (TagKindExtensions.QUEST, QuestTag.QUEST_SUMMARY),
                    ]
                ),
                QuestNameFilter(quest_name=quest_name),
                LastInventoryFilter(),
            ]
        ),
        generation_for="Action Choices",
        new_file=True,  # don't put this in the chat history. it is help content.
        streaming=False,
    )
    return block
