"""
Заполнение справочников при первом запуске (seed data).
Каждая запись вставляется в отдельном SAVEPOINT — ошибка одной
не прерывает всю транзакцию и не портит сессию.
"""
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError


def init_dictionary_data(db: Session):
    """Заполнить все справочные таблицы начальными данными."""
    _seed_all(db)
    try:
        db.commit()
    except Exception:
        db.rollback()


def _add(db: Session, Model, records: list):
    """
    Безопасная вставка записей справочника.
    Пропускает уже существующие. Каждая запись — отдельный savepoint.
    """
    for rec in records:
        try:
            existing = db.query(Model).filter(Model.id == rec["id"]).first()
            if not existing:
                db.add(Model(**rec))
                db.flush()          # проверяем ограничения немедленно
        except IntegrityError:
            db.rollback()           # откат только этой записи
        except Exception:
            db.rollback()


def _seed_all(db: Session):
    from src.models.dictionaries.goal_status             import GoalStatus
    from src.models.dictionaries.goal_priority           import GoalPriority
    from src.models.dictionaries.goal_repeat_type        import GoalRepeatType
    from src.models.dictionaries.goal_fail_behavior      import GoalFailBehavior
    from src.models.dictionaries.habit_type              import HabitType
    from src.models.dictionaries.habit_mode              import HabitMode
    from src.models.dictionaries.habit_status            import HabitStatus
    from src.models.dictionaries.block_level             import BlockLevel
    from src.models.dictionaries.focus_session_status    import FocusSessionStatus
    from src.models.dictionaries.notification_type       import NotificationType
    from src.models.dictionaries.notification_delivery_status import NotificationDeliveryStatus
    from src.models.dictionaries.completion_object_type  import CompletionObjectType
    from src.models.dictionaries.system_log_event_type   import SystemLogEventType

    _add(db, GoalStatus, [
        {"id": 1, "code": "ACTIVE",    "name_ru": "Активна",    "sort_order": 1},
        {"id": 2, "code": "COMPLETED", "name_ru": "Выполнена",  "sort_order": 2},
        {"id": 3, "code": "OVERDUE",   "name_ru": "Просрочена", "sort_order": 3},
        {"id": 4, "code": "CANCELED",  "name_ru": "Отменена",   "sort_order": 4},
        {"id": 5, "code": "DELETED",   "name_ru": "Удалена",    "sort_order": 5},
        {"id": 6, "code": "ARCHIVED",  "name_ru": "В архиве",   "sort_order": 6},
    ])
    _add(db, GoalPriority, [
        {"id": 1, "code": "HIGH",   "name_ru": "Высокий", "sort_order": 1},
        {"id": 2, "code": "MEDIUM", "name_ru": "Средний", "sort_order": 2},
        {"id": 3, "code": "LOW",    "name_ru": "Низкий",  "sort_order": 3},
    ])
    _add(db, GoalRepeatType, [
        {"id": 1, "code": "NONE",    "name_ru": "Разовая",      "sort_order": 1},
        {"id": 2, "code": "DAILY",   "name_ru": "Ежедневная",   "sort_order": 2},
        {"id": 3, "code": "WEEKLY",  "name_ru": "Еженедельная", "sort_order": 3},
        {"id": 4, "code": "MONTHLY", "name_ru": "Ежемесячная",  "sort_order": 4},
    ])
    _add(db, GoalFailBehavior, [
        {"id": 1, "code": "MOVE", "name_ru": "Перенести",                "sort_order": 1},
        {"id": 2, "code": "SKIP", "name_ru": "Отметить как пропущенную", "sort_order": 2},
    ])
    _add(db, HabitType, [
        {"id": 1, "code": "DAILY",   "name_ru": "Ежедневная",   "sort_order": 1},
        {"id": 2, "code": "WEEKLY",  "name_ru": "Еженедельная", "sort_order": 2},
        {"id": 3, "code": "MONTHLY", "name_ru": "Ежемесячная",  "sort_order": 3},
    ])
    _add(db, HabitMode, [
        {"id": 1, "code": "BINARY",       "name_ru": "Бинарная",       "sort_order": 1},
        {"id": 2, "code": "QUANTITATIVE", "name_ru": "Количественная", "sort_order": 2},
    ])
    _add(db, HabitStatus, [
        {"id": 1, "code": "ACTIVE",   "name_ru": "Активна",   "sort_order": 1},
        {"id": 2, "code": "ARCHIVED", "name_ru": "В архиве",  "sort_order": 2},
        {"id": 3, "code": "DISABLED", "name_ru": "Отключена", "sort_order": 3},
        {"id": 4, "code": "DELETED",  "name_ru": "Удалена",   "sort_order": 4},
    ])
    _add(db, BlockLevel, [
        {"id": 1, "code": "FULL",  "name_ru": "Полная блокировка", "sort_order": 1},
        {"id": 2, "code": "PAUSE", "name_ru": "Приостановка",      "sort_order": 2},
        {"id": 3, "code": "LIMIT", "name_ru": "Ограничение",       "sort_order": 3},
    ])
    _add(db, FocusSessionStatus, [
        {"id": 1, "code": "COMPLETED",   "name_ru": "Завершена успешно", "sort_order": 1},
        {"id": 2, "code": "CANCELLED",   "name_ru": "Прервана",          "sort_order": 2},
        {"id": 3, "code": "INTERRUPTED", "name_ru": "Прервана внешне",   "sort_order": 3},
    ])
    _add(db, NotificationType, [
        {"id": 1, "code": "REMINDER", "name_ru": "Напоминание", "sort_order": 1},
        {"id": 2, "code": "SYSTEM",   "name_ru": "Системное",   "sort_order": 2},
    ])
    _add(db, NotificationDeliveryStatus, [
        {"id": 1, "code": "SENT",    "name_ru": "Отправлено", "sort_order": 1},
        {"id": 2, "code": "PENDING", "name_ru": "Ожидает",    "sort_order": 2},
        {"id": 3, "code": "FAILED",  "name_ru": "Ошибка",     "sort_order": 3},
    ])
    _add(db, CompletionObjectType, [
        {"id": 1, "code": "GOAL",  "name_ru": "Цель",     "sort_order": 1},
        {"id": 2, "code": "HABIT", "name_ru": "Привычка", "sort_order": 2},
    ])
    _add(db, SystemLogEventType, [
        {"id": 1, "code": "ERROR",   "name_ru": "Ошибка",         "sort_order": 1},
        {"id": 2, "code": "WARNING", "name_ru": "Предупреждение", "sort_order": 2},
        {"id": 3, "code": "INFO",    "name_ru": "Информация",     "sort_order": 3},
    ])
