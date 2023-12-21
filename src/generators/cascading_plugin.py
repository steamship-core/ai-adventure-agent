from typing import Callable, Mapping, List, Dict, Optional

from pydantic import PrivateAttr
from steamship import PluginInstance

InstanceProvider = Callable[[], PluginInstance]


class ExhaustedPluginsException(Exception):
    def __init__(self, exceptions: Mapping[str, Exception]):
        self.exceptions = exceptions
        message = []
        for plugin_name, e in exceptions.items():
            message.append(f"- {plugin_name}: {str(e)}\n")
        message_str = f"Plugin calls exhausted with following exceptions:\n{''.join(message)}"
        super().__init__(message_str)


class CascadingPlugin(PluginInstance):
    """
    A PluginInstance wrapper which takes multiple providers of PluginInstances and cascades calls to them upon failure.
    """
    instance_providers: List[InstanceProvider]
    _exception_map: Dict[str, Exception] = PrivateAttr(dict())
    _instance_provider_ix: int = PrivateAttr(0)
    _cached_instance: Optional[PluginInstance] = PrivateAttr(None)

    def _advance_instance(self) -> None:
        self._instance_provider_ix += 1
        self._cached_instance = None
        if self._instance_provider_ix >= len(self.instance_providers):
            # Don't make it so that this will never succeed again, let it recover on a basic heuristic.
            # TODO this / current_instance could be smarter to try the preferred ones on a backoff
            self._instance_provider_ix = 0
            raise ExhaustedPluginsException(self._exception_map)

    def _current_instance(self) -> PluginInstance:
        if not self._cached_instance:
            self._cached_instance = self.instance_providers[self._instance_provider_ix]()
        return self._cached_instance

    # The following methods are wrapping around the API for PluginInstance.
    # TODO this could be hacked up in a more general sense to check for Callables and pass these through in getattr?

    def tag(self, *args, **kwargs):
        while True:
            try:
                return self._current_instance().tag(*args, **kwargs)
            except Exception as e:
                self._exception_map[self._current_instance().plugin_id] = e
                self._advance_instance()

    def generate(self, *args, **kwargs):
        while True:
            try:
                return self._current_instance().generate(*args, **kwargs)
            except Exception as e:
                self._exception_map[self._current_instance().plugin_id] = e
                self._advance_instance()

    def delete(self, *args, **kwargs):
        while True:
            try:
                return self._current_instance().delete(*args, **kwargs)
            except Exception as e:
                self._exception_map[self._current_instance().plugin_id] = e
                self._advance_instance()

    def train(self, *args, **kwargs):
        raise NotImplementedError("The `train` endpoint is not implemented for CascadingPlugin")

    def refresh_init_status(self, *args, **kwargs):
        while True:
            try:
                return self._current_instance().refresh_init_status(*args, **kwargs)
            except Exception as e:
                self._exception_map[self._current_instance().plugin_id] = e
                self._advance_instance()

    def wait_for_init(self, *args, **kwargs):
        while True:
            try:
                return self._current_instance().wait_for_init(*args, **kwargs)
            except Exception as e:
                self._exception_map[self._current_instance().plugin_id] = e
                self._advance_instance()
