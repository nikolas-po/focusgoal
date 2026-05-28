"""Интеграционные тесты NotificationService (ТЗ FR-006)"""
import pytest
from datetime import time
from unittest.mock import patch, MagicMock
from src.services.notification_service import NotificationService


class TestNotificationService:
    def test_send_calls_plyer(self, db_session):
        svc = NotificationService(db_session)
        with patch("src.services.notification_service.HAS_PLYER", True),              patch("src.services.notification_service.plyer_notify") as mock_notify:
            svc.send("Test", "Message")
            mock_notify.notify.assert_called_once()

    def test_quiet_mode_suppresses(self, db_session):
        svc = NotificationService(db_session)
        svc.set_quiet(True, start=time(0, 0), end=time(23, 59))
        with patch("src.services.notification_service.plyer_notify") as mock_notify:
            svc.send("Test", "Message")
            mock_notify.notify.assert_not_called()

    def test_quiet_mode_disabled(self, db_session):
        svc = NotificationService(db_session)
        svc.set_quiet(False)
        with patch("src.services.notification_service.HAS_PLYER", True),              patch("src.services.notification_service.plyer_notify") as mock_notify:
            svc.send("Test", "Message")
            mock_notify.notify.assert_called_once()

    def test_send_goal_reminder(self, db_session):
        svc = NotificationService(db_session)
        with patch.object(svc, "send") as mock_send:
            svc.send_focus_complete(25)
            mock_send.assert_called_once()

    def test_scheduler_start_stop(self):
        try:
            NotificationService.start_scheduler()
            assert NotificationService._scheduler is not None
        finally:
            NotificationService.stop_scheduler()
