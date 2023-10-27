from abc import ABC, abstractmethod

from pydantic.main import BaseModel
from steamship.agents.schema import AgentContext

from schema.evaluations import ObstacleEvaluation, QuestEvaluation


class QuestGenerator(BaseModel, ABC):

    @abstractmethod
    def generate_quest_intro(self, context: AgentContext):
        pass

    @abstractmethod
    def create_quest_obstacle(self, context: AgentContext):
        pass

    @abstractmethod
    def generate_obstacle_text(self, context: AgentContext):
        pass

    @abstractmethod
    def evaluate_user_input_for_obstacle(self, user_input: str, context: AgentContext) -> ObstacleEvaluation:
        pass

    @abstractmethod
    def generate_obstacle_failed_text(self, user_input: str, context: AgentContext):
        pass

    @abstractmethod
    def generate_obstacle_passed_text(self, user_input: str, context: AgentContext):
        pass

    @abstractmethod
    def evaluate_user_input_for_quest(self, user_input: str, context: AgentContext) -> QuestEvaluation:
        pass

    @abstractmethod
    def generate_quest_incomplete_text(self, user_input: str, context: AgentContext):
        pass

    @abstractmethod
    def generate_quest_complete_text(self, user_input: str, context: AgentContext):
        pass

    @abstractmethod
    def generate_item_for_quest(self, context: AgentContext):
        pass
