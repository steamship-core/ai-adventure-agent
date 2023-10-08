"""Utilities for interacting with the AgentContext.

IMPORTANT:

This file is one of the key design principles of the game.
The helper functions within mediate light-weight access to global game state using only the AgentContext.

USAGE:

The following things should ALWAYS be done via these functions:
- getting / setting of game state
- getting or generators
- manipulations on active chat histories

That way these can as global accessors into the shared AgentContext object that is passed around, with persistence
layered on top to boot.

That reduces the need of the game code to perform verbose plumbing operations.
"""
import logging
from typing import List, Optional, Union

from steamship import Block, MimeTypes, PluginInstance, Tag
from steamship.agents.logging import AgentLogging
from steamship.agents.schema import ChatHistory, ChatLLM, FinishAction
from steamship.agents.schema.agent import AgentContext
from steamship.data import TagValueKey
from steamship.utils.kv_store import KeyValueStore

_STORY_GENERATOR_KEY = "story-generator"
_FUNCTION_CAPABLE_LLM = (
    "function-capable-llm"  # This could be distinct from the one generating the story.
)
_BACKGROUND_MUSIC_GENERATOR_KEY = "background-music-generator"
_BACKGROUND_IMAGE_GENERATOR_KEY = "background-image-generator"
_PROFILE_IMAGE_GENERATOR_KEY = "profile-image-generator"
_NARRATION_GENERATOR_KEY = "narration-generator"
_SERVER_SETTINGS_KEY = "server-settings"
_game_state_KEY = "user-settings"


def with_story_generator(
    instance: PluginInstance, context: AgentContext
) -> AgentContext:
    context.metadata[_STORY_GENERATOR_KEY] = instance
    return context


def with_function_capable_llm(instance: ChatLLM, context: AgentContext) -> AgentContext:
    context.metadata[_FUNCTION_CAPABLE_LLM] = instance
    return context


def with_background_music_generator(
    instance: PluginInstance, context: AgentContext
) -> AgentContext:
    context.metadata[_BACKGROUND_MUSIC_GENERATOR_KEY] = instance
    return context


def with_background_image_generator(
    instance: PluginInstance, context: AgentContext
) -> AgentContext:
    context.metadata[_BACKGROUND_IMAGE_GENERATOR_KEY] = instance
    return context


def with_profile_image_generator(
    instance: PluginInstance, context: AgentContext
) -> AgentContext:
    context.metadata[_PROFILE_IMAGE_GENERATOR_KEY] = instance
    return context


def with_narration_generator(
    instance: PluginInstance, context: AgentContext
) -> AgentContext:
    context.metadata[_NARRATION_GENERATOR_KEY] = instance
    return context


def with_server_settings(
    server_settings: "ServerSettings", context: AgentContext  # noqa: F821
) -> "ServerSettings":  # noqa: F821
    context.metadata[_SERVER_SETTINGS_KEY] = server_settings
    return context


def with_game_state(
    server_settings: "GameState", context: AgentContext  # noqa: F821
) -> "GameState":  # noqa: F821
    context.metadata[_game_state_KEY] = server_settings
    return context


def get_story_text_generator(
    context: AgentContext, default: Optional[PluginInstance] = None
) -> Optional[PluginInstance]:
    return context.metadata.get(_STORY_GENERATOR_KEY, default)


def get_background_music_generator(
    context: AgentContext, default: Optional[PluginInstance] = None
) -> Optional[PluginInstance]:
    return context.metadata.get(_BACKGROUND_MUSIC_GENERATOR_KEY, default)


def get_background_image_generator(
    context: AgentContext, default: Optional[PluginInstance] = None
) -> Optional[PluginInstance]:
    return context.metadata.get(_BACKGROUND_IMAGE_GENERATOR_KEY, default)


def get_profile_image_generator(
    context: AgentContext, default: Optional[PluginInstance] = None
) -> Optional[PluginInstance]:
    return context.metadata.get(_PROFILE_IMAGE_GENERATOR_KEY, default)


def get_audio_narration_generator(
    context: AgentContext, default: Optional[PluginInstance] = None
) -> Optional[PluginInstance]:
    return context.metadata.get(_NARRATION_GENERATOR_KEY, default)


def get_server_settings(
    context: AgentContext, default: Optional["ServerSettings"] = None  # noqa: F821
) -> Optional["ServerSettings"]:  # noqa: F821
    return context.metadata.get(_SERVER_SETTINGS_KEY, default)


def get_game_state(
    context: AgentContext, default: Optional["GameState"] = None  # noqa: F821
) -> Optional["GameState"]:  # noqa: F821
    logging.info(
        f"Refreshing Game State from workspace {context.client.config.workspace_handle}.",
        extra={
            AgentLogging.IS_MESSAGE: True,
            AgentLogging.MESSAGE_TYPE: AgentLogging.THOUGHT,
            AgentLogging.MESSAGE_AUTHOR: AgentLogging.AGENT,
        },
    )

    return context.metadata.get(_game_state_KEY, default)


def save_game_state(game_state, context: AgentContext):
    """Save GameState to the KeyValue store."""

    # Save it to the KV Store
    key = "GameState"
    value = game_state.dict()
    kv = KeyValueStore(context.client, key)
    kv.set(key, value)

    # Also save it to the context
    context.metadata[_game_state_KEY] = game_state


def get_current_quest(context: AgentContext) -> Optional["Quest"]:  # noqa: F821
    """Return current Quest, or None."""

    game_state = get_game_state(context)

    if not game_state:
        return None

    if not game_state.current_quest:
        return None

    for quest in game_state.quests or []:
        if quest.name == game_state.current_quest:
            return quest

    return None


def get_current_conversant(
    context: AgentContext,
) -> Optional["NpcCharacter"]:  # noqa: F821
    """Return the NpcCharacter of the current conversation, or None."""
    game_state = get_game_state(context)

    if not game_state:
        return None

    if not game_state.in_conversation_with:
        return None

    if not game_state.camp:
        return None

    if not game_state.camp.npcs:
        return None

    for npc in game_state.camp.npcs or []:
        if npc.name == game_state.in_conversation_with:
            return npc

    return None


def switch_history_to_current_conversant(
    context: AgentContext,
) -> AgentContext:  # noqa: F821
    """Return the NpcCharacter of the current conversation, or None."""
    npc = get_current_conversant(context)

    if npc:
        logging.info(
            f"Switching to NPC Chat History: {npc.name}.",
            extra={
                AgentLogging.IS_MESSAGE: True,
                AgentLogging.MESSAGE_TYPE: AgentLogging.THOUGHT,
                AgentLogging.MESSAGE_AUTHOR: AgentLogging.AGENT,
            },
        )
        history = ChatHistory.get_or_create(
            context.client, {"id": npc.name}, [], searchable=True
        )
        context.chat_history = history
    return context


def switch_history_to_current_quest(
    context: AgentContext,
) -> AgentContext:  # noqa: F821
    """Return the NpcCharacter of the current conversation, or None."""
    quest = get_current_quest(context)

    if quest:
        logging.info(
            f"Switching to Quest Chat History: {quest.name}.",
            extra={
                AgentLogging.IS_MESSAGE: True,
                AgentLogging.MESSAGE_TYPE: AgentLogging.THOUGHT,
                AgentLogging.MESSAGE_AUTHOR: AgentLogging.AGENT,
            },
        )
        history = ChatHistory.get_or_create(
            context.client, {"id": f"quest:{quest.name}"}, [], searchable=True
        )
        context.chat_history = history
    return context


def get_function_capable_llm(
    context: AgentContext, default: Optional[ChatLLM] = None  # noqa: F821
) -> Optional[ChatLLM]:  # noqa: F821
    return context.metadata.get(_FUNCTION_CAPABLE_LLM, default)


def _key_for_question(blocks: List[Block], key: Optional[str] = None) -> str:
    """The lookup key for a particular question being asked of the user.

    This can be used to tell -- in the "future" -- if the value being awaited is the same as the value last solicited.
    """
    if key:
        return key

    ret = ""
    for block in blocks:
        if block.text:
            ret += block.text
        else:
            ret += block.url
    return ret


class FinishActionException(Exception):
    """Thrown when a piece of code wishes to pop the stack all the way up to the enclosing Agent or AgentService.

    The intended result is that the agent treat teh Exception as a FinishAction, emitting the response.

    It is up to the throwing party to do any additional data preparation (e.g. see await_ask) related.
    """

    action: FinishAction

    def __init__(self, action: FinishAction):
        super().__init__()
        self.action = action


def await_ask(
    question: Union[str, List[Block]], context: AgentContext, key: Optional[str] = None
):
    """Asks the user a question. Can be used like `input` in Python.

    USAGE:

        name = ask_user("What is your name?")

    RESULT:

        * If the key is equal to game_state.await_ask_key object, then this method immediately returns the last
          user input from the chat_history. This means the agent has awoken after asking a question and getting input.
          We also clear the game_state.await_ask_key bit.
        * If the key is not equal to game_state.await_ask_key, then this method (1) sets it, (2) emits the question
          to the chat history file, and (3) throws a FinishActionException.

        The FinishActionException is handled by the enclosing Agent.
    """
    BASE_TAGS = [
        Tag(
            kind="request-id",
            name=context.request_id,
            value={TagValueKey.STRING_VALUE.value: context.request_id},
        )
    ]

    # Make sure question is List[Block]
    if isinstance(question, str):
        output = [Block(text=question, tags=BASE_TAGS)]
    else:
        output = question

    key = _key_for_question(output)

    # Check if we have ALREADY asked about this key!
    game_state = get_game_state(context)

    logging.info(
        f"Seeking input with await_ask key: {key}.",
        extra={
            AgentLogging.IS_MESSAGE: True,
            AgentLogging.MESSAGE_TYPE: AgentLogging.THOUGHT,
            AgentLogging.MESSAGE_AUTHOR: AgentLogging.AGENT,
        },
    )

    if game_state.await_ask_key == key:
        logging.info(
            f"Last await_ask key matches: {game_state.await_ask_key}.",
            extra={
                AgentLogging.IS_MESSAGE: True,
                AgentLogging.MESSAGE_TYPE: AgentLogging.THOUGHT,
                AgentLogging.MESSAGE_AUTHOR: AgentLogging.AGENT,
            },
        )

        # Assume we've already asked! Let's return the last user response.
        if context.chat_history and context.chat_history.last_user_message:
            if context.chat_history.last_user_message.text:
                game_state.await_ask_key = None
                save_game_state(game_state, context)
                answer = context.chat_history.last_user_message.text
                logging.info(
                    f"Using last user input as answer: {answer}.",
                    extra={
                        AgentLogging.IS_MESSAGE: True,
                        AgentLogging.MESSAGE_TYPE: AgentLogging.THOUGHT,
                        AgentLogging.MESSAGE_AUTHOR: AgentLogging.AGENT,
                    },
                )
                return answer

    # Otherwise we set the key and throw the asking exception
    game_state.await_ask_key = key

    logging.info(
        f"Awaiting user response with await_ask key: {game_state.await_ask_key}.",
        extra={
            AgentLogging.IS_MESSAGE: True,
            AgentLogging.MESSAGE_TYPE: AgentLogging.THOUGHT,
            AgentLogging.MESSAGE_AUTHOR: AgentLogging.AGENT,
        },
    )

    save_game_state(game_state, context)
    raise FinishActionException(action=FinishAction(output=output))


def emit(output: Union[str, Block, List[Block]], context: AgentContext):
    """Emits a message to the user."""
    if isinstance(output, str):
        output = [Block(text=output)]
    elif isinstance(output, Block):
        output = [output]

    for func in context.emit_funcs:
        logging.info(
            f"Emitting via function '{func.__name__}' for context: {context.id}"
        )
        func(output, context.metadata)


def append_to_chat_history_and_emit(
    context: AgentContext,
    text: str = None,
    tags: List[Tag] = None,
    content: Union[str, bytes] = None,
    url: Optional[str] = None,
    mime_type: Optional[MimeTypes] = None,
    block: Optional[Block] = None,
) -> Block:
    """Append a new block and then trigger an emit() for sync clients.

    Adds a new `blocks` option for in-process generation output.

    TODO / NOTA BENE:
      While we could just generate directly into the ChatHistory, this currently (1) doesn't enable
      us to ensure those generated blocks have the correct chat-related tags, and (2) doesn't give us a way to
      notify non-streaming clients of these new blocks.

    This is the preferred way to send an assistant message to the user if:

    - One is streaming messages amidst operation (e.g. streaming back several messages)
    - One wishes to still support non-streaming clients, including the development CLI

    The streaming client will see the message because of the chat history append operation.
    The non-streaming client will see the message because of the emit() operation.
    """

    if block is None:
        block = context.chat_history.append_assistant_message(
            text=text, tags=tags, content=content, url=url, mime_type=mime_type
        )
        emit(block, context)
        return block
    else:
        if block.is_video() or block.is_audio() or block.is_image():
            # TODO: This is super inefficient.
            _block = context.chat_history.append_assistant_message(
                url=block.to_public_url(), tags=block.tags, mime_type=block.mime_type
            )
        else:
            _block = context.chat_history.append_assistant_message(
                text=block.text, tags=block.tags, mime_type=block.mime_type
            )
        try:
            emit(_block, context)
        except BaseException as e:
            logging.error(e)
            logging.error(
                "Ted note: I'm not going to fix right now but I think the engine is having trouble returning /raw for a text block."
            )
        return block


class RunNextAgentException(Exception):
    """Thrown when a piece of code, anywhere, wishes to pop the stack all the way up to the AgentService and
    activate the next agent.

    In the game, this is used when a Tool (which starts/ends different states of the game) wishes to proceed
    IMMEDIATELY to the next state without waiting for user input to trigger it.

    Otherwise, there would be the following awkward moment in gameplay:

    User: Go on a quest
    CampAgent -> StartQuestTool: OK! Let's quest! <modifies game state>
    ...
    (PROBLEM: User now needs to say something back to re-trigger the next phrase, which will be QuestAgent).

    Instead, the following can happen:

    User: Go on a quest
    CampAgent -> StartQuestTool: OK! Let's Quest! <modifies game state> <throws RunNextAgentException>
    QuestAgent: The quest begins! You walk out of camp and gather your items.. You've got..

    Basically: this is a way to let the game take two conversational turns right in a row, the second affected
    by the state transition of the first.
    """

    action: FinishAction

    def __init__(self, action: FinishAction):
        super().__init__()
        self.action = action
