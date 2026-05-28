"""Интеграционные тесты репозиториев"""
import pytest
from src.repositories.goal_repository import GoalRepository
from src.repositories.habit_repository import HabitRepository
from src.repositories.user_repository import UserRepository
from datetime import date


class TestGoalRepository:
    def test_create_and_fetch(self, db_session, test_user):
        repo = GoalRepository(db_session)
        goal = repo.create(user_id=test_user["id"], name="Репо-цель",
                           priority_id=1, status_id=1)
        assert goal.id is not None
        fetched = repo.get_by_id(goal.id)
        assert fetched.name == "Репо-цель"

    def test_soft_delete(self, db_session, test_user, test_goal):
        repo = GoalRepository(db_session)
        ok = repo.soft_delete(test_goal.id, test_user["id"])
        assert ok is True
        g = repo.get_by_id(test_goal.id)
        assert g.status_id == 5

    def test_get_by_user(self, db_session, test_user, test_goal):
        repo = GoalRepository(db_session)
        goals = repo.get_by_user(test_user["id"])
        assert any(g.id == test_goal.id for g in goals)

    def test_filter_by_status(self, db_session, test_user):
        repo = GoalRepository(db_session)
        repo.create(user_id=test_user["id"], name="Активная цель",
                    priority_id=2, status_id=1)
        active = repo.get_by_user(test_user["id"], {"status_id": 1})
        assert all(g.status_id == 1 for g in active)

    def test_count_by_status(self, db_session, test_user):
        repo = GoalRepository(db_session)
        count = repo.count_by_status(test_user["id"], 1)
        assert isinstance(count, int)


class TestHabitRepository:
    def test_create_and_fetch(self, db_session, test_user):
        repo = HabitRepository(db_session)
        habit = repo.create(user_id=test_user["id"], name="Репо-привычка",
                            type_id=1, mode_id=1, status_id=1, start_date=date.today())
        assert habit.id is not None
        assert repo.get_by_id(habit.id).name == "Репо-привычка"

    def test_get_by_user(self, db_session, test_user, test_habit):
        repo = HabitRepository(db_session)
        habits = repo.get_by_user(test_user["id"])
        assert any(h.id == test_habit.id for h in habits)

    def test_get_active(self, db_session, test_user, test_habit):
        repo = HabitRepository(db_session)
        active = repo.get_active_habits(test_user["id"])
        assert all(h.status_id == 1 for h in active)


class TestUserRepository:
    def test_get_by_nickname(self, db_session, test_user):
        repo = UserRepository(db_session)
        user = repo.get_by_nickname("testuser")
        assert user is not None
        assert user.id == test_user["id"]

    def test_nickname_exists_true(self, db_session, test_user):
        repo = UserRepository(db_session)
        assert repo.nickname_exists("testuser") is True

    def test_nickname_exists_false(self, db_session):
        repo = UserRepository(db_session)
        assert repo.nickname_exists("definitely_no_such_user_xyz") is False
