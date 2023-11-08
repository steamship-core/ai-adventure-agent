import logging

from steamship.agents.logging import AgentLogging
from steamship.agents.schema import AgentContext

from utils.context_utils import get_game_state, save_game_state


def record_and_throw_unrecoverable_error(e: BaseException, context: AgentContext):
    logging.exception(e)
    logging.error(
        f"Got unexpected exception. {e}",
        extra={
            AgentLogging.IS_MESSAGE: True,
            AgentLogging.MESSAGE_TYPE: AgentLogging.THOUGHT,
            AgentLogging.MESSAGE_AUTHOR: AgentLogging.AGENT,
        },
    )

    # Attempt to transition the game state to ERROR
    try:
        gs = get_game_state(context)
        gs.unrecoverable_error = f"Got unexpected exception. {e}"
        save_game_state(gs, context)
    except BaseException as e2:
        logging.error(
            f"Unable to persist game state of ERROR. {e2}",
            extra={
                AgentLogging.IS_MESSAGE: True,
                AgentLogging.MESSAGE_TYPE: AgentLogging.THOUGHT,
                AgentLogging.MESSAGE_AUTHOR: AgentLogging.AGENT,
            },
        )
    raise e
