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

from steamship import Block, PluginInstance
from steamship.agents.llms.openai import ChatOpenAI
from steamship.agents.logging import AgentLogging
from steamship.agents.schema import ChatHistory, ChatLLM, FinishAction
from steamship.agents.schema.agent import AgentContext
from steamship.utils.kv_store import KeyValueStore

from schema.game_state import GameState
from schema.server_settings import ServerSettings
from utils.tags import QuestIdTag

_STORY_GENERATOR_KEY = "story-generator"
_FUNCTION_CAPABLE_LLM = (
    "function-capable-llm"  # This could be distinct from the one generating the story.
)
_BACKGROUND_MUSIC_GENERATOR_KEY = "background-music-generator"
_NARRATION_GENERATOR_KEY = "narration-generator"
_SERVER_SETTINGS_KEY = "server-settings"
_GAME_STATE_KEY = "user-settings"


def with_function_capable_llm(instance: ChatLLM, context: AgentContext) -> AgentContext:
    context.metadata[_FUNCTION_CAPABLE_LLM] = instance
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


def get_story_text_generator(
    context: AgentContext, default: Optional[PluginInstance] = None
) -> Optional[PluginInstance]:
    generator = context.metadata.get(_STORY_GENERATOR_KEY, default)

    if not generator:
        # Lazily create
        server_settings: ServerSettings = get_server_settings(context)
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
    server_settings = get_server_settings(context)
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
        config = {}
        if plugin_handle == "elevenlabs":
            config["voice_id"] = server_settings.narration_voice_id
        generator = context.client.use_plugin(plugin_handle, config=config)
        context.metadata[_NARRATION_GENERATOR_KEY] = generator

    return generator


def get_server_settings(
    context: AgentContext,
) -> "ServerSettings":  # noqa: F821
    logging.debug(
        f"Refreshing Server Settings from workspace {context.client.config.workspace_handle}.",
        extra={
            AgentLogging.IS_MESSAGE: True,
            AgentLogging.MESSAGE_TYPE: AgentLogging.THOUGHT,
            AgentLogging.MESSAGE_AUTHOR: AgentLogging.AGENT,
        },
    )

    if _SERVER_SETTINGS_KEY in context.metadata:
        return context.metadata.get(_SERVER_SETTINGS_KEY)

    # Get it from the KV Store
    kv = KeyValueStore(context.client, _SERVER_SETTINGS_KEY)
    value = kv.get(_SERVER_SETTINGS_KEY)

    if value:
        logging.debug(f"Parsing Server Settings from stored value: {value}")
        server_settings = ServerSettings.parse_obj(value)
        context.metadata[_SERVER_SETTINGS_KEY] = server_settings
        return server_settings
    else:
        logging.debug("Creating new Server Settings -- one didn't exist!")
        server_settings = ServerSettings()
        context.metadata[_SERVER_SETTINGS_KEY] = server_settings
        return server_settings


def get_game_state(context: AgentContext) -> Optional["GameState"]:  # noqa: F821
    logging.debug(
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
    kv = KeyValueStore(context.client, _GAME_STATE_KEY)
    value = kv.get(_GAME_STATE_KEY)

    if value:
        logging.debug(f"Parsing game state from stored value: \n{value}")
        game_state = GameState.parse_obj(value)
        context.metadata[_GAME_STATE_KEY] = game_state
        return game_state
    else:
        logging.debug("Creating new game state -- one didn't exist!")
        game_state = GameState()
        context.metadata[_GAME_STATE_KEY] = game_state

        # FOR QUICK DEBUGGING
        # game_state.player = HumanCharacter()
        # game_state.player.name = "Dave"
        # game_state.player.description = "he is tall"
        # game_state.player.background = "he's a guy"
        ####

        return game_state


def save_server_settings(server_settings, context: AgentContext):
    """Save ServerSettings to the KeyValue store."""

    logging.debug(
        f"Saving Server Settings from workspace {context.client.config.workspace_handle}.",
        extra={
            AgentLogging.IS_MESSAGE: True,
            AgentLogging.MESSAGE_TYPE: AgentLogging.THOUGHT,
            AgentLogging.MESSAGE_AUTHOR: AgentLogging.AGENT,
        },
    )

    # Save it to the KV Store
    value = server_settings.dict()
    kv = KeyValueStore(context.client, _SERVER_SETTINGS_KEY)
    kv.set(_SERVER_SETTINGS_KEY, value)

    # Also save it to the context
    context.metadata[_SERVER_SETTINGS_KEY] = server_settings


def save_game_state(game_state, context: AgentContext):
    """Save GameState to the KeyValue store."""

    logging.debug(
        f"Saving Game State from workspace {context.client.config.workspace_handle}.",
        extra={
            AgentLogging.IS_MESSAGE: True,
            AgentLogging.MESSAGE_TYPE: AgentLogging.THOUGHT,
            AgentLogging.MESSAGE_AUTHOR: AgentLogging.AGENT,
        },
    )

    # Save it to the KV Store
    value = game_state.dict()
    kv = KeyValueStore(context.client, _GAME_STATE_KEY)
    kv.set(_GAME_STATE_KEY, value)

    # Also save it to the context
    context.metadata[_GAME_STATE_KEY] = game_state


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
            f"Switching to Quest Chat History: {quest.name}",
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
    question: Union[str, List[Block]],
    context: AgentContext,
    key_suffix: str = "",
    prompt_prologue: Optional[str] = "",
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
    # Check if we have ALREADY asked about this key!
    game_state = get_game_state(context)

    base_tags = []

    if game_state.current_quest:
        # Make sure we're tagging this for request rehydration
        base_tags.append(QuestIdTag(game_state.current_quest))

    # Make sure question is List[Block]
    if isinstance(question, str):
        output = [Block(text=question, tags=base_tags)]
    else:
        for block in question:
            if not block.tags:
                block.tags = []
            block.tags.extend(base_tags)
        output = question

    key = _key_for_question(output) + key_suffix

    logging.info(
        f"Seeking input with await_ask key: {key}",
        extra={
            AgentLogging.IS_MESSAGE: True,
            AgentLogging.MESSAGE_TYPE: AgentLogging.THOUGHT,
            AgentLogging.MESSAGE_AUTHOR: AgentLogging.AGENT,
        },
    )

    if game_state.await_ask_key == key:
        logging.info(
            f"Last await_ask key matches: {game_state.await_ask_key}",
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
                    f"Using last user input as answer: {answer}",
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
        f"Awaiting user response with await_ask key: {game_state.await_ask_key}",
        extra={
            AgentLogging.IS_MESSAGE: True,
            AgentLogging.MESSAGE_TYPE: AgentLogging.THOUGHT,
            AgentLogging.MESSAGE_AUTHOR: AgentLogging.AGENT,
        },
    )

    save_game_state(game_state, context)

    if prompt_prologue:
        output.insert(0, Block(text=prompt_prologue))

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
