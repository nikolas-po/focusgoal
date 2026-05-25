"""Интеграционные тесты базы данных"""
import pytest
from sqlalchemy import inspect


class TestDatabaseStructure:
    def test_all_tables_created(self, db_engine):
        inspector = inspect(db_engine)
        tables = inspector.get_table_names()
        required = [
            "user", "goal", "habit", "focus_session",
            "blocked_app", "completion_log",
            "notification_schedule", "system_log",
            "goal_status", "goal_priority", "goal_repeat_type",
            "goal_fail_behavior", "habit_type", "habit_mode",
            "habit_status", "block_level", "focus_session_status",
            "notification_type", "notification_delivery_status",
            "completion_object_type", "system_log_event_type",
        ]
        for t in required:
            assert t in tables, f"Таблица '{t}' не найдена"

    def test_goal_statuses_seeded(self, db_session):
        from src.models.dictionaries.goal_status import GoalStatus
        statuses = db_session.query(GoalStatus).all()
        assert len(statuses) == 6

    def test_habit_types_seeded(self, db_session):
        from src.models.dictionaries.habit_type import HabitType
        types = db_session.query(HabitType).all()
        assert len(types) == 3

    def test_goal_foreign_key(self, db_session, test_user, test_goal):
        from src.models.goal import Goal
        g = db_session.query(Goal).filter(Goal.id == test_goal.id).first()
        assert g.user_id == test_user["id"]

    def test_cascade_delete(self, db_session, test_user):
        from src.models.goal import Goal
        from src.models.user import User
        goal = Goal(user_id=test_user["id"], name="Каскадная",
                    priority_id=1, status_id=1)
        db_session.add(goal)
        db_session.commit()
        gid = goal.id
        user = db_session.query(User).filter(User.id == test_user["id"]).first()
        db_session.delete(user)
        db_session.commit()
        result = db_session.query(Goal).filter(Goal.id == gid).first()
        assert result is None

    def test_statistics_empty_user(self, db_session):
        from src.services.statistics_service import StatisticsService
        st = StatisticsService(db_session).get_dashboard_statistics(999999)
        assert st["goals"]["total"] == 0
        assert st["habits"]["total"] == 0
        assert st["focus"]["total_minutes"] == 0
