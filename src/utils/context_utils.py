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
import json
import logging
from typing import List, Optional, Union

from steamship import Block, PluginInstance
from steamship.agents.llms.openai import ChatOpenAI
from steamship.agents.logging import AgentLogging
from steamship.agents.schema import ChatHistory, ChatLLM, FinishAction
from steamship.agents.schema.agent import AgentContext
from steamship.utils.kv_store import KeyValueStore

from generators.image_generator import ImageGenerator
from schema.game_state import GameState

_STORY_GENERATOR_KEY = "story-generator"
_FUNCTION_CAPABLE_LLM = (
    "function-capable-llm"  # This could be distinct from the one generating the story.
)
_BACKGROUND_MUSIC_GENERATOR_KEY = "background-music-generator"
_IMAGE_GENERATOR_KEY = "image-generator"
_NARRATION_GENERATOR_KEY = "narration-generator"
_SERVER_SETTINGS_KEY = "server-settings"
_GAME_STATE_KEY = "user-settings"


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


def with_image_generator(
    image_generator: ImageGenerator, context: AgentContext
) -> AgentContext:
    context.metadata[_IMAGE_GENERATOR_KEY] = image_generator
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
    game_state: "GameState", context: AgentContext  # noqa: F821
) -> "AgentContext":  # noqa: F821
    context.metadata[_GAME_STATE_KEY] = game_state
    return context


def get_image_generator(context: AgentContext) -> Optional[ImageGenerator]:
    return context.metadata.get(_IMAGE_GENERATOR_KEY, None)


def get_story_text_generator(
    context: AgentContext, default: Optional[PluginInstance] = None
) -> Optional[PluginInstance]:
    generator = context.metadata.get(_STORY_GENERATOR_KEY, default)

    if not generator:
        # Lazily create
        server_settings = get_server_settings(context)
        game_state = get_game_state(context)
        preferences = game_state.preferences

        open_ai_models = ["gpt-3.5-turbo", "gpt-4"]
        replicate_models = ["dolly_v2", "llama_v2"]

        model_name = server_settings._select_model(
            open_ai_models + replicate_models,
            default=server_settings.default_story_model,
            preferred=preferences.narration_model,
        )

        plugin_handle = None
        if model_name in open_ai_models:
            plugin_handle = "gpt-4"
        elif model_name in replicate_models:
            plugin_handle = "replicate-llm"

        generator = context.client.use_plugin(
            plugin_handle,
            config={
                "model": model_name,
                "max_tokens": server_settings.default_story_max_tokens,
                "temperature": server_settings.default_story_temperature,
            },
        )

        context.metadata[_STORY_GENERATOR_KEY] = generator

    return generator


def get_background_music_generator(
    context: AgentContext, default: Optional[PluginInstance] = None
) -> Optional[PluginInstance]:
    generator = context.metadata.get(_BACKGROUND_MUSIC_GENERATOR_KEY, default)

    if not generator:
        # Lazily create
        server_settings = get_server_settings(context)
        game_state = get_game_state(context)
        preferences = game_state.preferences

        plugin_handle = server_settings._select_model(
            ["music-generator"],  # Valid models
            default=server_settings.default_narration_model,
            preferred=preferences.background_music_model,
        )
        generator = context.client.use_plugin(plugin_handle)
        context.metadata[_BACKGROUND_MUSIC_GENERATOR_KEY] = generator

    return generator


def get_audio_narration_generator(
    context: AgentContext, default: Optional[PluginInstance] = None
) -> Optional[PluginInstance]:
    generator = context.metadata.get(_NARRATION_GENERATOR_KEY, default)

    if not generator:
        # Lazily create
        server_settings = get_server_settings(context)
        game_state = get_game_state(context)
        preferences = game_state.preferences

        plugin_handle = server_settings._select_model(
            ["elevenlabs"],
            default=server_settings.default_narration_model,
            preferred=preferences.narration_model,
        )
        generator = context.client.use_plugin(plugin_handle)
        context.metadata[_NARRATION_GENERATOR_KEY] = generator

    return generator


def get_server_settings(
    context: AgentContext, default: Optional["ServerSettings"] = None  # noqa: F821
) -> Optional["ServerSettings"]:  # noqa: F821
    return context.metadata.get(_SERVER_SETTINGS_KEY, default)


def get_game_state(context: AgentContext) -> Optional["GameState"]:  # noqa: F821
    logging.info(
        f"Refreshing Game State from workspace {context.client.config.workspace_handle}.",
        extra={
            AgentLogging.IS_MESSAGE: True,
            AgentLogging.MESSAGE_TYPE: AgentLogging.THOUGHT,
            AgentLogging.MESSAGE_AUTHOR: AgentLogging.AGENT,
        },
    )

    if _GAME_STATE_KEY in context.metadata:
        return context.metadata.get(_GAME_STATE_KEY)

    # Get it from the KV Store
    key = "GameState"
    kv = KeyValueStore(context.client, key)
    value = kv.get(key)

    if value:
        print("Parsing game state from stored value")
        print(value)
        game_state = GameState.parse_obj(value)
        context.metadata[_GAME_STATE_KEY] = game_state
        return game_state
    else:
        print("Creating new game state -- one didn't exist!")
        game_state = GameState()
        context.metadata[_GAME_STATE_KEY] = game_state

        # FOR QUICK DEBUGGING
        # game_state.player = HumanCharacter()
        # game_state.player.name = "Dave"
        # game_state.player.motivation = "Doing cool things"
        # game_state.player.description = "he is tall"
        # game_state.player.background = "he's a guy"
        # game_state.tone = "funny"
        # game_state.genre = "adventure"
        ####

        return game_state


def save_game_state(game_state, context: AgentContext):
    """Save GameState to the KeyValue store."""

    # Save it to the KV Store
    key = "GameState"
    value = game_state.dict()
    kv = KeyValueStore(context.client, key)
    kv.set(key, value)

    # Also save it to the context
    context.metadata[_GAME_STATE_KEY] = game_state

    print("Just saved game state to", json.dumps(value, indent="\t"))


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
    llm = context.metadata.get(_FUNCTION_CAPABLE_LLM, default)
    if not llm:
        # Lazy create
        llm = ChatOpenAI(context.client)
        context.metadata[_FUNCTION_CAPABLE_LLM] = llm
    return llm


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


class FinishActionException(Exception):  # noqa: N818
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
    base_tags = []

    # Make sure question is List[Block]
    if isinstance(question, str):
        output = [Block(text=question, tags=base_tags)]
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


class RunNextAgentException(Exception):  # noqa: N818
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
