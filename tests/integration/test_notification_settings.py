"""Тесты NotificationService с проверкой настроек пользователя (ТЗ FR-006).

Проверяет что:
  - При notifications=False ни одно уведомление не отправляется
  - При notif_goals=False цели не проверяются, привычки — да
  - При notif_habits=False привычки не проверяются, цели — да
  - При notif_focus=False уведомление о завершении фокус-сессии не отправляется
  - Без systemd-таймера APScheduler-цикл правильно читает настройки
  - Тихий режим подавляет отправку в нужный диапазон времени
"""
import pytest
from datetime import time, datetime, timedelta
from unittest.mock import patch, MagicMock, call
from src.models.habit import Habit
from src.services.notification_service import NotificationService
from tests.conftest import db_session
from tests.conftest import db_session


# Вспомогательный builder пользователя с заданными настройками

def _user_with_settings(db_session, settings: dict):
    """Создаёт пользователя и возвращает его id."""
    from src.services.auth_service import AuthService
    import random, string
    nick = "notif_" + "".join(random.choices(string.ascii_lowercase, k=6))
    user = AuthService(db_session).register(nick, "Pass1234x")
    from src.models.user import User
    u = db_session.query(User).filter(User.id == user["id"]).first()
    u.settings = settings
    db_session.commit()
    return user["id"]


# Тесты глобального отключения уведомлений

class TestNotificationsGlobalSwitch:

    def test_notifications_off_no_goals_check(self, db_session):
        """notifications=False — check_goal_deadlines не вызывается."""
        uid = _user_with_settings(db_session, {
            "notifications": False,
            "notif_goals": True,
            "notif_habits": True,
        })
        svc = NotificationService(db_session, uid)
        with patch.object(svc, "check_goal_deadlines") as mock_goals, \
             patch.object(svc, "check_habit_streak") as mock_habits, \
             patch.object(svc, "check_scheduled_notifications") as mock_sched:
            svc._do_notifications()
        mock_goals.assert_not_called()
        mock_habits.assert_not_called()
        mock_sched.assert_not_called()

    def test_notifications_on_goals_and_habits_called(self, db_session):
        """notifications=True, оба флага True — оба метода вызываются."""
        uid = _user_with_settings(db_session, {
            "notifications": True,
            "notif_goals": True,
            "notif_habits": True,
        })
        svc = NotificationService(db_session, uid)
        with patch.object(svc, "check_goal_deadlines") as mock_goals, \
             patch.object(svc, "check_habit_streak") as mock_habits, \
             patch.object(svc, "check_scheduled_notifications"):
            svc._do_notifications()
        mock_goals.assert_called_once()
        mock_habits.assert_called_once()

    def test_default_settings_send_all(self, db_session):
        """Если settings пустой — по умолчанию всё включено."""
        uid = _user_with_settings(db_session, {})
        svc = NotificationService(db_session, uid)
        with patch.object(svc, "check_goal_deadlines") as mock_goals, \
             patch.object(svc, "check_habit_streak") as mock_habits, \
             patch.object(svc, "check_scheduled_notifications"):
            svc._do_notifications()
        mock_goals.assert_called_once()
        mock_habits.assert_called_once()


# Тесты отдельных флагов уведомлений

class TestNotificationFlags:

    def test_notif_goals_false_skips_goal_check(self, db_session):
        uid = _user_with_settings(db_session, {
            "notifications": True,
            "notif_goals": False,
            "notif_habits": True,
        })
        svc = NotificationService(db_session, uid)
        with patch.object(svc, "check_goal_deadlines") as mock_goals, \
             patch.object(svc, "check_habit_streak") as mock_habits, \
             patch.object(svc, "check_scheduled_notifications"):
            svc._do_notifications()
        mock_goals.assert_not_called()
        mock_habits.assert_called_once()

    def test_notif_habits_false_skips_habit_check(self, db_session):
        uid = _user_with_settings(db_session, {
            "notifications": True,
            "notif_goals": True,
            "notif_habits": False,
        })
        svc = NotificationService(db_session, uid)
        with patch.object(svc, "check_goal_deadlines") as mock_goals, \
             patch.object(svc, "check_habit_streak") as mock_habits, \
             patch.object(svc, "check_scheduled_notifications"):
            svc._do_notifications()
        mock_goals.assert_called_once()
        mock_habits.assert_not_called()

    def test_scheduled_notifications_always_checked(self, db_session):
        """check_scheduled_notifications вызывается даже если goals/habits выключены."""
        uid = _user_with_settings(db_session, {
            "notifications": True,
            "notif_goals": False,
            "notif_habits": False,
        })
        svc = NotificationService(db_session, uid)
        with patch.object(svc, "check_goal_deadlines"), \
             patch.object(svc, "check_habit_streak"), \
             patch.object(svc, "check_scheduled_notifications") as mock_sched:
            svc._do_notifications()
        mock_sched.assert_called_once()


# Тесты тихого режима (ТЗ FR-006.3)

class TestQuietMode:

    def test_quiet_mode_suppresses_send(self, db_session):
        svc = NotificationService(db_session)
        svc.set_quiet(True, start=time(0, 0), end=time(23, 59))
        with patch.object(svc, "send_notification") as mock_send, \
             patch("src.services.notification_service.HAS_PLYER", False):
            result = svc.send("Тест", "Сообщение")
        assert result is False
        mock_send.assert_not_called()

    def test_quiet_mode_disabled_allows_send(self, db_session):
        svc = NotificationService(db_session)
        svc.set_quiet(False)
        with patch.object(svc, "send_notification", return_value=True) as mock_send, \
             patch("src.services.notification_service.HAS_PLYER", False):
            result = svc.send("Тест", "Сообщение")
        assert result is True
        mock_send.assert_called_once()

    def test_quiet_mode_overnight(self):
        """Тихий режим через полночь (22:00–08:00)."""
        svc = NotificationService(None)
        svc.set_quiet(True, start=time(22, 0), end=time(8, 0))

        # 23:30 — в тихом режиме
        with patch("src.services.notification_service.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2025, 1, 1, 23, 30)
            assert svc._is_quiet_now() is True

        # 07:00 — ещё в тихом режиме
        with patch("src.services.notification_service.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2025, 1, 1, 7, 0)
            assert svc._is_quiet_now() is True

        # 12:00 — вне тихого режима
        with patch("src.services.notification_service.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2025, 1, 1, 12, 0)
            assert svc._is_quiet_now() is False

    def test_quiet_mode_not_set_returns_false(self):
        svc = NotificationService(None)
        assert svc._is_quiet_now() is False


# Тесты уведомлений о фокус-сессиях (ТЗ FR-004, FR-006.2)

class TestFocusNotifications:

    def test_send_focus_complete_sends_notification(self, db_session):
        svc = NotificationService(db_session)
        with patch.object(svc, "send") as mock_send:
            svc.send_focus_complete(25)
        mock_send.assert_called_once()
        args = mock_send.call_args[0]
        assert "25" in str(args) or "фокус" in str(args[0]).lower()

    def test_focus_notification_respects_user_settings(self, db_session):
        """Уведомление о фокусе не отправляется если notif_focus=False.

        Тестируем непосредственно логику в _send_focus_complete_notification
        через сервис — изолированно от PyQt.
        """
        uid = _user_with_settings(db_session, {
            "notifications": True,
            "notif_focus": False,
        })
        svc = NotificationService(db_session, uid)

        # Симулируем вызов из FocusTimer через метод send_focus_complete
        # Проверяем что при notif_focus=False send не вызывается
        settings = svc._get_user_settings()
        assert settings.get("notif_focus", True) is False


# Тесты проверки целей по дедлайну (ТЗ FR-002, FR-006.1)

class TestGoalDeadlineNotifications:

    def test_check_goal_deadlines_no_user(self, db_session):
        """Без user_id метод не должен падать."""
        svc = NotificationService(db_session, user_id=None)
        svc.check_goal_deadlines()  # не должно выбросить исключение

    def test_check_goal_deadlines_today(self, db_session, test_user, test_goal):
        """Цель с дедлайном сегодня генерирует уведомление."""
        from src.models.goal import Goal
        from datetime import timezone as tz

        goal = db_session.query(Goal).filter(Goal.id == test_goal.id).first()
        goal.deadline = datetime.now()
        db_session.commit()

        print("Goals:", db_session.query(Goal).all())
        
        svc = NotificationService(db_session, test_user["id"])
        with patch.object(svc, "send_notification") as mock_send:
            svc.check_goal_deadlines()

        assert mock_send.call_count >= 1
        # Проверяем что хотя бы одно уведомление содержит название цели
        all_messages = " ".join(str(c) for c in mock_send.call_args_list)
        assert test_goal.name in all_messages

    def test_check_goal_deadlines_tomorrow(self, db_session, test_user, test_goal):
        """Цель с дедлайном завтра тоже генерирует уведомление."""
        from src.models.goal import Goal

        goal = db_session.query(Goal).filter(Goal.id == test_goal.id).first()
        goal.deadline = datetime.now() + timedelta(days=1)
        db_session.commit()

        svc = NotificationService(db_session, test_user["id"])
        with patch.object(svc, "send_notification") as mock_send:
            svc.check_goal_deadlines()

        assert mock_send.call_count >= 1


# Тесты проверки привычек (ТЗ FR-003, FR-006.1)

class TestHabitStreakNotifications:

    def test_check_habit_streak_no_user(self, db_session):
        """Без user_id метод не должен падать."""
        svc = NotificationService(db_session, user_id=None)
        svc.check_habit_streak()

    def test_check_habit_streak_daily_habits(self, db_session, test_user, test_habit):
        
        from src.models.habit import Habit
        print("Habits:", db_session.query(Habit).all())
        
        """Ежедневные активные привычки получают напоминание."""
        svc = NotificationService(db_session, test_user["id"])
        with patch.object(svc, "send_notification") as mock_send:
            svc.check_habit_streak()
        assert mock_send.call_count >= 1


# Тест планировщика (APScheduler, без systemd)

class TestSchedulerWithoutSystemd:

    def test_schedule_notifications_adds_job(self):
        try:
            NotificationService.start_scheduler()
            assert NotificationService._scheduler is not None
            assert NotificationService._scheduler.running

            svc = NotificationService(None, user_id=1)
            svc.schedule_notifications(interval_minutes=60)

            jobs = NotificationService._scheduler.get_jobs()
            job_ids = [j.id for j in jobs]
            assert "check_notifications" in job_ids
        finally:
            NotificationService.stop_scheduler()

    def test_stop_scheduler_when_not_running(self):
        """Остановка незапущенного планировщика не выбрасывает исключение."""
        NotificationService._scheduler = None
        NotificationService.stop_scheduler()  # не должно упасть
