"""Тесты FocusService (ТЗ FR-009)"""
import pytest
from datetime import datetime
from src.services.focus_service import FocusService
from src.models.focus_session import FocusSession


class TestFocusService:
    def test_start_session(self, db_session, test_user):
        svc = FocusService(db_session)
        session = svc.start_session(test_user["id"], 25)
        assert session.id is not None
        assert session.planned_duration == 25
        assert session.status_id == 1
        assert session.user_id == test_user["id"]

    def test_start_session_with_goal(self, db_session, test_user, test_goal):
        svc = FocusService(db_session)
        session = svc.start_session(test_user["id"], 50, goal_id=test_goal.id)
        assert session.goal_id == test_goal.id

    def test_stop_session_completed(self, db_session, test_user):
        svc = FocusService(db_session)
        session = svc.start_session(test_user["id"], 25)
        # Вручную сдвигаем start_time для теста
        session.start_time = datetime(2024, 1, 1, 10, 0, 0)
        db_session.commit()
        result = svc.stop_session(session.id, status_id=1)
        assert result.status_id == 1
        assert result.actual_duration is not None

    def test_stop_session_cancelled(self, db_session, test_user):
        svc = FocusService(db_session)
        session = svc.start_session(test_user["id"], 25)
        result = svc.stop_session(session.id, status_id=2)
        assert result.status_id == 2

    def test_get_sessions(self, db_session, test_user):
        svc = FocusService(db_session)
        svc.start_session(test_user["id"], 25)
        svc.start_session(test_user["id"], 50)
        sessions = svc.get_sessions(test_user["id"])
        assert len(sessions) >= 2

    def test_get_running_processes(self, db_session):
        svc = FocusService(db_session)
        procs = svc.get_running_processes()
        assert isinstance(procs, list)
        if procs:
            assert "pid" in procs[0]
            assert "name" in procs[0]

    def test_session_duration_constraint(self, db_session, test_user):
        """Длительность сессии должна быть 1–480 минут"""
        svc = FocusService(db_session)
        with pytest.raises(Exception):
            svc.start_session(test_user["id"], 0)

    def test_session_isolation(self, db_session, test_user):
        """Сессии другого пользователя недоступны"""
        svc = FocusService(db_session)
        svc.start_session(test_user["id"], 25)
        other_sessions = svc.get_sessions(99999)
        assert len(other_sessions) == 0
