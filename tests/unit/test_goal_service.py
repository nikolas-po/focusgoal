"""Тесты GoalService (ТЗ FR-002)"""
import pytest
from src.services.goal_service import GoalService
from datetime import datetime, timedelta


class TestGoalService:
    def test_create_goal(self, db_session, test_user):
        svc = GoalService(db_session)
        goal = svc.create_goal(test_user["id"], {
            "name": "Выучить Python",
            "priority_id": 1,
            "status_id": 1,
        })
        assert goal.id is not None
        assert goal.name == "Выучить Python"
        assert goal.user_id == test_user["id"]

    def test_get_goals(self, db_session, test_user, test_goal):
        svc = GoalService(db_session)
        goals = svc.get_goals(test_user["id"])
        assert len(goals) >= 1
        assert any(g.id == test_goal.id for g in goals)

    def test_get_goals_filter_by_status(self, db_session, test_user, test_goal):
        svc = GoalService(db_session)
        active = svc.get_goals(test_user["id"], {"status_id": 1})
        assert all(g.status_id == 1 for g in active)

    def test_update_goal(self, db_session, test_user, test_goal):
        svc = GoalService(db_session)
        updated = svc.update_goal(test_goal.id, test_user["id"],
                                  {"name": "Обновлённое название"})
        assert updated is not None
        assert updated.name == "Обновлённое название"

    def test_update_goal_wrong_user(self, db_session, test_goal):
        svc = GoalService(db_session)
        result = svc.update_goal(test_goal.id, 9999, {"name": "Взлом"})
        assert result is None

    def test_delete_goal(self, db_session, test_user, test_goal):
        svc = GoalService(db_session)
        result = svc.delete_goal(test_goal.id, test_user["id"])
        assert result is True
        goals = svc.get_goals(test_user["id"])
        deleted = next((g for g in goals if g.id == test_goal.id), None)
        if deleted:
            assert deleted.status_id == 5

    def test_complete_goal(self, db_session, test_user, test_goal):
        svc = GoalService(db_session)
        completed = svc.complete_goal(test_goal.id, test_user["id"])
        assert completed is not None
        assert completed.status_id == 2

    def test_goal_name_min_length(self, db_session, test_user):
        svc = GoalService(db_session)
        with pytest.raises(Exception):
            svc.create_goal(test_user["id"], {"name": "ab", "status_id": 1})
