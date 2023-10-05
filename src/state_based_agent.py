import logging
from abc import ABC, abstractmethod

from pydantic import Field, ConfigDict
from steamship import Steamship
from steamship.agents.schema import Agent, AgentContext, Action, FinishAction
from steamship.utils.kv_store import KeyValueStore


class StateBasedAgent(Agent, ABC):
	START = "start"
	FINISHED = "finished"

	def get_state(self, state_store: KeyValueStore) -> str:
		state_dict = state_store.get("state")
		if state_dict != None:
			return state_dict.get("state", self.START)
		else:
			return self.START


	def set_state(self, next_state: str, state_store: KeyValueStore):
		state_store.set("state", {'state': next_state})

	def next_action(self, context: AgentContext) -> Action:
		state_store = KeyValueStore(
			context.client, store_identifier=f"StateStore_{context.id}"
		)
		current_state = self.get_state(state_store=state_store)
		logging.info(f"Executing state: {current_state}")
		if current_state != self.FINISHED:
			current_state_func = getattr(self, current_state)
			next_state = current_state_func(context=context)
			self.set_state(next_state, state_store=state_store)
			logging.info(f"Next state: {next_state}")
		return FinishAction(output=[])


	@abstractmethod
	def start(self, context: AgentContext):
		pass





