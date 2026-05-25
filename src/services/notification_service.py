"""Полная реализация системы уведомлений (in-app + systemd)"""
import os
import sys
from pathlib import Path
from datetime import datetime, timezone, time
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

try:
    from plyer import notification as plyer_notify
    HAS_PLYER = True
except Exception:
    plyer_notify = None
    HAS_PLYER = False


class NotificationService:
    """Сервис уведомлений (in-app и системные)"""
    
    _scheduler = None
    _jobs = {}

    @classmethod
    def start_scheduler(cls):
        """Запустить background scheduler"""
        if cls._scheduler is None:
            cls._scheduler = BackgroundScheduler(daemon=True)
            cls._scheduler.start()
            print("[NotificationService] Планировщик запущен")

    @classmethod
    def stop_scheduler(cls):
        """Остановить scheduler при выходе из приложения"""
        if cls._scheduler and cls._scheduler.running:
            try:
                cls._scheduler.shutdown(wait=False)
                print("[NotificationService] Планировщик остановлен")
            except Exception as e:
                print(f"[NotificationService] Ошибка при остановке: {e}")
            cls._scheduler = None

    def __init__(self, db):
        self.db = db
        self._quiet_mode = False
        self._quiet_start = None
        self._quiet_end = None

    def set_quiet(self, enabled: bool, start: time = None, end: time = None):
        self._quiet_mode = enabled
        self._quiet_start = start
        self._quiet_end = end
        return True

    def _is_quiet_now(self):
        if not self._quiet_mode or self._quiet_start is None or self._quiet_end is None:
            return False
        current_time = datetime.now().time()
        if self._quiet_start <= self._quiet_end:
            return self._quiet_start <= current_time <= self._quiet_end
        return current_time >= self._quiet_start or current_time <= self._quiet_end

    def send(self, title: str, message: str, urgency: str = "normal"):
        if self._is_quiet_now():
            print("[NotificationService] Уведеноение подавлено в тихий час")
            return False

        if HAS_PLYER and plyer_notify:
            try:
                plyer_notify.notify(
                    title=title,
                    message=message,
                    app_name="FocusGoal",
                    timeout=5,
                )
                return True
            except Exception as e:
                print(f"[NotificationService] Plyer notify failed: {e}")

        return self.send_notification(title, message, urgency)

    def send_focus_complete(self, minutes: int):
        return self.send(
            "Фокус завершен",
            f"Вы завершили фокусную сессию на {minutes} минут.",
        )

    def send_notification(self, title: str, message: str, urgency: str = "normal"):
        """Отправить уведомление в systemd"""
        try:
            import subprocess
            # notify-send отправляет уведомление в систему
            subprocess.run([
                "notify-send",
                "-u", urgency,
                "-a", "FocusGoal",
                "-i", "dialog-information",
                title,
                message
            ], timeout=5, check=False)
            print(f"[Notification] {title}: {message}")
            return True
        except Exception as e:
            print(f"[NotificationService] Не удалось отправить уведомление: {e}")
            return False

    def check_goal_deadlines(self):
        """Проверить сроки целей и отправить уведомления"""
        try:
            from src.models.goal import Goal
            from datetime import datetime, timedelta, timezone
            
            now = datetime.now()
            today = now.date()
            
            # Цели с дедлайном сегодня
            goals_today = self.db.query(Goal).filter(
                Goal.deadline == today,
                Goal.status_id == 1  # только активные
            ).all()
            
            for goal in goals_today:
                msg = f"Сегодня нужно выполнить цель: {goal.name}"
                self.send_notification("Напоминание о цели", msg)
            
            # Цели с дедлайном завтра
            tomorrow = today + timedelta(days=1)
            goals_tomorrow = self.db.query(Goal).filter(
                Goal.deadline == tomorrow,
                Goal.status_id == 1
            ).all()
            
            for goal in goals_tomorrow:
                msg = f"Завтра дедлайн цели: {goal.name}"
                self.send_notification("Напоминание на завтра", msg)
            
            # Просроченные цели
            goals_overdue = self.db.query(Goal).filter(
                Goal.deadline < today,
                Goal.status_id.in_([1, 3])  # активные и просроченные
            ).all()
            
            for goal in goals_overdue:
                msg = f"Просрочена цель: {goal.name}"
                self.send_notification("Просроченная цель!", msg, "critical")
            
            print(f"[NotificationService] Проверка целей: {len(goals_today)} сегодня, {len(goals_tomorrow)} завтра, {len(goals_overdue)} просрочено")
        except Exception as e:
            print(f"[NotificationService] Ошибка при проверке целей: {e}")

    def check_habit_streak(self):
        """Проверить привычки и напомнить о них"""
        try:
            from src.models.habit import Habit
            from datetime import datetime, timezone
            
            habits = self.db.query(Habit).filter(Habit.status_id == 1).all()
            
            for habit in habits:
                if habit.type_id == 1:  # ежедневная (DAILY)
                    msg = f"Не забудьте о привычке: {habit.name}"
                    self.send_notification("Напоминание о привычке", msg)
            
            print(f"[NotificationService] Проверка привычек: {len(habits)} активных")
        except Exception as e:
            print(f"[NotificationService] Ошибка при проверке привычек: {e}")

    def check_scheduled_notifications(self):
        try:
            from src.models.notification import NotificationSchedule
            from datetime import datetime, timedelta

            now = datetime.now()
            # Просроченные   игнорируются.
            time_window_start = now - timedelta(minutes=5)
            time_window_end = now + timedelta(minutes=1)

            pending = self.db.query(NotificationSchedule).filter(
                NotificationSchedule.delivery_status_id == 2,
                NotificationSchedule.send_at.between(time_window_start, time_window_end)
            ).all()

            for n in pending:
                self.send_notification("Напоминание", n.content)
                # Запись остаётся в БД, но при следующем запуске она уже не попадёт в окно

            if pending:
                print(f"[NotificationService] Отправлено {len(pending)} уведомлений")

        except Exception as e:
            print(f"[NotificationService] Ошибка при проверке уведомлений: {e}")

    def schedule_daily_backup(self, hour: int = 2, minute: int = 0):
        """Расписание для ежедневного бэкапа в 2:00 ночи"""
        try:
            if self._scheduler is None:
                return
            
            job_id = "daily_backup"
            # Удалить старую работу если есть
            if job_id in self._jobs:
                self._scheduler.remove_job(job_id)
            
            # Добавить новую работу
            trigger = CronTrigger(hour=hour, minute=minute)
            job = self._scheduler.add_job(
                self._do_backup,
                trigger=trigger,
                id=job_id,
                name="Ежедневный бэкап",
                replace_existing=True
            )
            self._jobs[job_id] = job
            print(f"[NotificationService] Бэкап запланирован на {hour:02d}:{minute:02d}")
        except Exception as e:
            print(f"[NotificationService] Ошибка при планировании бэкапа: {e}")

    def schedule_notifications(self, interval_minutes: int = 30):
        """Расписание для проверки уведомлений каждые N минут"""
        try:
            if self._scheduler is None:
                return
            
            job_id = "check_notifications"
            if job_id in self._jobs:
                self._scheduler.remove_job(job_id)
            
            trigger = IntervalTrigger(minutes=interval_minutes)
            job = self._scheduler.add_job(
                self._do_notifications,
                trigger=trigger,
                id=job_id,
                name="Проверка уведомлений",
                replace_existing=True
            )
            self._jobs[job_id] = job
            print(f"[NotificationService] Уведомления запланированы каждые {interval_minutes} минут")
        except Exception as e:
            print(f"[NotificationService] Ошибка при планировании уведомлений: {e}")

    @staticmethod
    def _do_backup():
        """Выполнить бэкап"""
        try:
            from src.services.backup_service import BackupService
            from src.config.database import SessionLocal
            db = SessionLocal()
            service = BackupService()
            backup_file = service.backup()
            db.close()
            print(f"[BackupService] Бэкап выполнен: {backup_file}")
        except Exception as e:
            print(f"[BackupService] Ошибка при бэкапе: {e}")

    def _do_notifications(self):
        """Выполнить проверку уведомлений"""
        try:
            self.check_scheduled_notifications()
            self.check_goal_deadlines()
            self.check_habit_streak()
        except Exception as e:
            print(f"[NotificationService] Ошибка при проверке уведомлений: {e}")