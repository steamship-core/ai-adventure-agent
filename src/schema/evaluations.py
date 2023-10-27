from enum import Enum, auto


class QuestEvaluation(str, Enum):
    NOT_RELEVANT = auto()
    QUEST_INCOMPLETE = auto()
    QUEST_FAILED = auto()
    QUEST_SUCCEEDED = auto()

    @staticmethod
    def from_str(label):
        match label:
            case "NOT_RELEVANT":
                return QuestEvaluation.NOT_RELATED
            case "QUEST_INCOMPLETE":
                return QuestEvaluation.QUEST_INCOMPLETE
            case "QUEST_FAILED":
                return QuestEvaluation.QUEST_FAILED
            case "QUEST_SUCCEEDED":
                return QuestEvaluation.QUEST_SUCCEEDED
        return QuestEvaluation.NOT_RELATED


class ObstacleEvaluation(str, Enum):
    NOT_RELEVANT = auto()
    OBSTACLE_NOT_OVERCOME = auto()
    OBSTACLE_OVERCOME = auto()

    @staticmethod
    def from_str(label):
        match label:
            case "NOT_RELEVANT":
                return ObstacleEvaluation.NOT_RELEVANT
            case "OBSTACLE_NOT_OVERCOME":
                return ObstacleEvaluation.OBSTACLE_NOT_OVERCOME
            case "OBSTACLE_OVERCOME":
                return ObstacleEvaluation.OBSTACLE_OVERCOME
        return ObstacleEvaluation.NOT_RELEVANT
