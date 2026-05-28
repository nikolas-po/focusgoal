"""Тесты HabitService (ТЗ FR-003)"""
import pytest
from src.services.habit_service import HabitService
from datetime import date


class TestHabitService:
    def test_create_habit(self, db_session, test_user):
        svc = HabitService(db_session)
        habit = svc.create_habit(test_user["id"], {
            "name": "Медитация",
            "type_id": 1,
            "mode_id": 1,
            "status_id": 1,
            "start_date": date.today(),
        })
        assert habit.id is not None
        assert habit.name == "Медитация"
        assert habit.current_streak == 0

    def test_get_habits(self, db_session, test_user, test_habit):
        svc = HabitService(db_session)
        habits = svc.get_habits(test_user["id"])
        assert any(h.id == test_habit.id for h in habits)

    def test_mark_completed(self, db_session, test_user, test_habit):
        svc = HabitService(db_session)
        result = svc.mark_completed(test_habit.id, test_user["id"])
        assert result is not None
        assert result.current_streak == 1
        assert result.max_streak == 1

    def test_mark_completed_twice(self, db_session, test_user, test_habit):
        svc = HabitService(db_session)
        svc.mark_completed(test_habit.id, test_user["id"])
        result = svc.mark_completed(test_habit.id, test_user["id"])
        assert result.current_streak == 2

    def test_delete_habit(self, db_session, test_user, test_habit):
        svc = HabitService(db_session)
        result = svc.delete_habit(test_habit.id, test_user["id"])
        assert result is True
        habits = svc.get_habits(test_user["id"])
        deleted = next((h for h in habits if h.id == test_habit.id), None)
        if deleted:
            assert deleted.status_id == 4

    def test_update_habit(self, db_session, test_user, test_habit):
        svc = HabitService(db_session)
        updated = svc.update_habit(test_habit.id, test_user["id"],
                                   {"name": "Медитация обновлена"})
        assert updated is not None
        assert updated.name == "Медитация обновлена"

    def test_mark_completed_wrong_user(self, db_session, test_habit):
        svc = HabitService(db_session)
        result = svc.mark_completed(test_habit.id, 9999)
        assert result is None
