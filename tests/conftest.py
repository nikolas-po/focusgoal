"""Фикстуры pytest – SQLite in-memory с подменой JSONB"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# --- Подменяем JSONB → JSON для SQLite (ДО любого импорта моделей) ---
from sqlalchemy.dialects import postgresql
from sqlalchemy import JSON
postgresql.JSONB = JSON

# Теперь можно импортировать модели
from src.models.base import Base
import src.models  # noqa – регистрируем все модели


@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()
    _seed(session)
    session.commit()
    session.close()

    return engine


def _seed(session):
    from src.models.dictionaries.goal_status import GoalStatus
    from src.models.dictionaries.goal_priority import GoalPriority
    from src.models.dictionaries.goal_repeat_type import GoalRepeatType
    from src.models.dictionaries.goal_fail_behavior import GoalFailBehavior
    from src.models.dictionaries.habit_type import HabitType
    from src.models.dictionaries.habit_mode import HabitMode
    from src.models.dictionaries.habit_status import HabitStatus
    from src.models.dictionaries.block_level import BlockLevel
    from src.models.dictionaries.focus_session_status import FocusSessionStatus
    from src.models.dictionaries.notification_type import NotificationType
    from src.models.dictionaries.notification_delivery_status import NotificationDeliveryStatus
    from src.models.dictionaries.completion_object_type import CompletionObjectType
    from src.models.dictionaries.system_log_event_type import SystemLogEventType

    records = [
        (GoalStatus, [
            {"id": 1, "code": "ACTIVE",    "name_ru": "Активна",    "sort_order": 1},
            {"id": 2, "code": "COMPLETED", "name_ru": "Выполнена",  "sort_order": 2},
            {"id": 3, "code": "OVERDUE",   "name_ru": "Просрочена", "sort_order": 3},
            {"id": 4, "code": "CANCELED",  "name_ru": "Отменена",   "sort_order": 4},
            {"id": 5, "code": "DELETED",   "name_ru": "Удалена",    "sort_order": 5},
            {"id": 6, "code": "ARCHIVED",  "name_ru": "В архиве",   "sort_order": 6},
        ]),
        (GoalPriority, [
            {"id": 1, "code": "HIGH",   "name_ru": "Высокий", "sort_order": 1},
            {"id": 2, "code": "MEDIUM", "name_ru": "Средний", "sort_order": 2},
            {"id": 3, "code": "LOW",    "name_ru": "Низкий",  "sort_order": 3},
        ]),
        (GoalRepeatType, [
            {"id": 1, "code": "NONE",    "name_ru": "Разовая",      "sort_order": 1},
            {"id": 2, "code": "DAILY",   "name_ru": "Ежедневная",   "sort_order": 2},
            {"id": 3, "code": "WEEKLY",  "name_ru": "Еженедельная", "sort_order": 3},
            {"id": 4, "code": "MONTHLY", "name_ru": "Ежемесячная",  "sort_order": 4},
        ]),
        (GoalFailBehavior, [
            {"id": 1, "code": "MOVE", "name_ru": "Перенести", "sort_order": 1},
            {"id": 2, "code": "SKIP", "name_ru": "Отметить как пропущенную", "sort_order": 2},
        ]),
        (HabitType, [
            {"id": 1, "code": "DAILY",   "name_ru": "Ежедневная",   "sort_order": 1},
            {"id": 2, "code": "WEEKLY",  "name_ru": "Еженедельная", "sort_order": 2},
            {"id": 3, "code": "MONTHLY", "name_ru": "Ежемесячная",  "sort_order": 3},
        ]),
        (HabitMode, [
            {"id": 1, "code": "BINARY",       "name_ru": "Бинарная",       "sort_order": 1},
            {"id": 2, "code": "QUANTITATIVE", "name_ru": "Количественная", "sort_order": 2},
        ]),
        (HabitStatus, [
            {"id": 1, "code": "ACTIVE",   "name_ru": "Активна",   "sort_order": 1},
            {"id": 2, "code": "ARCHIVED", "name_ru": "В архиве",  "sort_order": 2},
            {"id": 3, "code": "DISABLED", "name_ru": "Отключена", "sort_order": 3},
            {"id": 4, "code": "DELETED",  "name_ru": "Удалена",   "sort_order": 4},
        ]),
        (BlockLevel, [
            {"id": 1, "code": "FULL",  "name_ru": "Полная блокировка", "sort_order": 1},
            {"id": 2, "code": "PAUSE", "name_ru": "Приостановка",      "sort_order": 2},
            {"id": 3, "code": "LIMIT", "name_ru": "Ограничение",       "sort_order": 3},
        ]),
        (FocusSessionStatus, [
            {"id": 1, "code": "COMPLETED",   "name_ru": "Завершена успешно", "sort_order": 1},
            {"id": 2, "code": "CANCELLED",   "name_ru": "Прервана",          "sort_order": 2},
            {"id": 3, "code": "INTERRUPTED", "name_ru": "Прервана внешне",   "sort_order": 3},
        ]),
        (NotificationType, [
            {"id": 1, "code": "REMINDER", "name_ru": "Напоминание", "sort_order": 1},
            {"id": 2, "code": "SYSTEM",   "name_ru": "Системное",   "sort_order": 2},
        ]),
        (NotificationDeliveryStatus, [
            {"id": 1, "code": "SENT",    "name_ru": "Отправлено", "sort_order": 1},
            {"id": 2, "code": "PENDING", "name_ru": "Ожидает",    "sort_order": 2},
            {"id": 3, "code": "FAILED",  "name_ru": "Ошибка",     "sort_order": 3},
        ]),
        (CompletionObjectType, [
            {"id": 1, "code": "GOAL",  "name_ru": "Цель",     "sort_order": 1},
            {"id": 2, "code": "HABIT", "name_ru": "Привычка", "sort_order": 2},
        ]),
        (SystemLogEventType, [
            {"id": 1, "code": "ERROR",   "name_ru": "Ошибка",         "sort_order": 1},
            {"id": 2, "code": "WARNING", "name_ru": "Предупреждение", "sort_order": 2},
            {"id": 3, "code": "INFO",    "name_ru": "Информация",     "sort_order": 3},
        ]),
    ]
    for Model, items in records:
        for item in items:
            if not session.query(Model).filter(Model.id == item["id"]).first():
                session.add(Model(**item))


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Сессия для каждого теста с откатом транзакции"""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def test_user(db_session):
    from src.services.auth_service import AuthService
    auth = AuthService(db_session)
    return auth.register("testuser", "Password123", "test@mail.ru", gdpr_consent=True)


@pytest.fixture
def test_goal(db_session, test_user):
    from src.services.goal_service import GoalService
    return GoalService(db_session).create_goal(test_user["id"], {
        "name": "Тестовая цель",
        "description": "Описание цели",
        "priority_id": 1,
        "status_id": 1,
    })


@pytest.fixture
def test_habit(db_session, test_user):
    from src.services.habit_service import HabitService
    from datetime import date
    return HabitService(db_session).create_habit(test_user["id"], {
        "name": "Тестовая привычка",
        "type_id": 1,
        "mode_id": 1,
        "status_id": 1,
        "start_date": date.today(),
    })