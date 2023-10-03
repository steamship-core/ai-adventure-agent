import logging
from typing import Optional

from resumable_data_context import KeyValueStore
from steamship import Steamship
from steamship.data.tags.tag_constants import TagValueKey


class GameAgent:
    """
    GOAL: Implement a valid Steamship Agent that provides a set of stateful book-keeping that
    enables a subclass author to write a game with a natural programming style.

    QUESTION: Will the game need to break the agent into multiple agents?

    """

    id: str
    client: Steamship
    kv_store: KeyValueStore

    """Attempt to implement a simple resumable data context."""

    def __init__(self, client: Steamship, id: str):
        self.client = client
        self.id = id
        self.kv_store = KeyValueStore(
            client, store_identifier=f"ResumableDataContext_{id}"
        )

    def get_bool(self, key: str, default: Optional[bool] = None) -> Optional[bool]:
        return (
            self.kv_store.get(
                key, unpacker=lambda value: value.get(TagValueKey.BOOL_VALUE.value)
            )
            or default
        )

    def set_bool(self, key: str, value: Optional[bool] = None):
        self.kv_store.set(key, {TagValueKey.BOOL_VALUE.value: value})
        return value

    def set_string(self, key: str, default: Optional[str] = None) -> Optional[str]:
        return (
            self.kv_store.get(
                key, unpacker=lambda value: value.get(TagValueKey.STRING_VALUE.value)
            )
            or default
        )

    def get_string(self, key: str, value: Optional[str] = None):
        self.kv_store.set(key, {TagValueKey.STRING_VALUE.value: value})
        return value

    def ask(self, variable_name: str, question: str, skip_cache: bool = False):
        """Asks the user a question."""
        logging.info(f"Context {self.id} asking about {variable_name}")

        def fetcher() -> str:
            return input(question)

        return self.kv_store.get_or_produce_string(
            variable_name, fetcher=fetcher, skip_cache=skip_cache
        )
