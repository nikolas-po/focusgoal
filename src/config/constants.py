"""Константы и классификаторы приложения"""
from enum import IntEnum


class GoalStatus(IntEnum):
    ACTIVE = 1
    COMPLETED = 2
    OVERDUE = 3
    CANCELED = 4
    DELETED = 5
    ARCHIVED = 6


class GoalPriority(IntEnum):
    HIGH = 1
    MEDIUM = 2
    LOW = 3


class GoalRepeatType(IntEnum):
    NONE = 1
    DAILY = 2
    WEEKLY = 3
    MONTHLY = 4


class GoalFailBehavior(IntEnum):
    MOVE = 1
    SKIP = 2


class HabitType(IntEnum):
    DAILY = 1
    WEEKLY = 2
    MONTHLY = 3


class HabitMode(IntEnum):
    BINARY = 1
    QUANTITATIVE = 2


class HabitStatus(IntEnum):
    ACTIVE = 1
    ARCHIVED = 2
    DISABLED = 3
    DELETED = 4


class BlockLevel(IntEnum):
    FULL = 1
    PAUSE = 2
    LIMIT = 3


class FocusSessionStatus(IntEnum):
    COMPLETED = 1
    CANCELLED = 2
    INTERRUPTED = 3


class NotificationType(IntEnum):
    REMINDER = 1
    SYSTEM = 2


class NotificationDeliveryStatus(IntEnum):
    SENT = 1
    PENDING = 2
    FAILED = 3


class CompletionObjectType(IntEnum):
    GOAL = 1
    HABIT = 2


class SystemLogEventType(IntEnum):
    ERROR = 1
    WARNING = 2
    INFO = 3


GOAL_STATUS_NAMES = {
    1: "Активна", 2: "Выполнена", 3: "Просрочена",
    4: "Отменена", 5: "Удалена", 6: "В архиве"
}

GOAL_PRIORITY_NAMES = {1: "Высокий", 2: "Средний", 3: "Низкий"}

HABIT_STATUS_NAMES = {
    1: "Активна", 2: "В архиве", 3: "Отключена", 4: "Удалена"
}

BLOCK_LEVEL_NAMES = {1: "Полная", 2: "Приостановка", 3: "Ограничение"}

REPEAT_TYPE_NAMES = {1: "Разовая", 2: "Ежедневная", 3: "Еженедельная", 4: "Ежемесячная"}

FAIL_BEHAVIOR_NAMES = {1: "Перенести", 2: "Отметить как пропущенную"}

HABIT_TYPE_NAMES = {1: "Ежедневная", 2: "Еженедельная", 3: "Ежемесячная"}

HABIT_MODE_NAMES = {1: "Бинарная", 2: "Количественная"}

FOCUS_SESSION_STATUS_NAMES = {
    1: "Завершена успешно", 2: "Прервана пользователем", 3: "Прервана внешне"
}
