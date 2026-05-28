"""Полная реализация системы уведомлений (in-app + systemd)"""
import os
import sys
from pathlib import Path
from datetime import datetime, time, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import func

try:
    from plyer import notification as plyer_notify
    HAS_PLYER = True
except Exception:
    plyer_notify = None


def _get_user_timezone(user_id: int | None = None) -> str:
    """Вернуть часовой пояс пользователя для расчёта локального времени."""
    if user_id is None:
        return "Europe/Moscow"
    try:
        from src.config.database import SessionLocal
        from src.models.user import User
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            return user.timezone if user and user.timezone else "Europe/Moscow"
        finally:
            db.close()
    except Exception:
        return "Europe/Moscow"


def _now_local(timezone_name: str | None = None) -> datetime:
    """Текущее локальное время как naive datetime в заданном часовом поясе."""
    try:
        from zoneinfo import ZoneInfo
        tz = timezone_name or "Europe/Moscow"
        return datetime.now(ZoneInfo(tz)).replace(tzinfo=None)
    except Exception:
        return datetime.now()


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

    def __init__(self, db, user_id: int = None):
        self.db = db
        self.user_id = user_id
        self._quiet_mode = False
        self._quiet_start = None
        self._quiet_end = None

    def set_quiet(self, enabled: bool, start: time = None, end: time = None):
        self._quiet_mode = enabled
        self._quiet_start = start
        self._quiet_end = end
        return True

    def _current_time(self):
        tz = _get_user_timezone(self.user_id)
        try:
            from zoneinfo import ZoneInfo
            now = datetime.now(ZoneInfo(tz))
        except Exception:
            now = datetime.now()
        return now.time()

    def _is_quiet_now(self):
        if not self._quiet_mode or self._quiet_start is None or self._quiet_end is None:
            return False
        current_time = self._current_time()
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

    def remove_reminder(self, job_id: str) -> bool:
        """Удалить задачу напоминания из планировщика (если есть)"""
        try:
            if self._scheduler and job_id in self._jobs:
                try:
                    self._scheduler.remove_job(job_id)
                except Exception:
                    pass
                self._jobs.pop(job_id, None)
                return True
        except Exception:
            pass
        return False

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
        """Проверить сроки целей и отправить уведомления.

        Использует переданную сессию self.db.
        Сравнения выполняются в часовом поясе пользователя.
        """
        try:
            from src.models.goal import Goal

            if self.user_id is None:
                return
            if self.db is None:
                print("[NotificationService] Нет сессии БД для проверки целей")
                return

            now = _now_local(_get_user_timezone(self.user_id))
            today = now.date()

            # Сегодняшние
            goals_today = self.db.query(Goal).filter(
                Goal.user_id == self.user_id,
                func.date(Goal.deadline) == today,
                Goal.status_id == 1,
            ).all()
            for goal in goals_today:
                self.send_notification(
                    "Напоминание о цели",
                    f"Сегодня нужно выполнить: {goal.name}",
                )

            # Завтрашние
            tomorrow = today + timedelta(days=1)
            goals_tomorrow = self.db.query(Goal).filter(
                Goal.user_id == self.user_id,
                func.date(Goal.deadline) == tomorrow,
                Goal.status_id == 1,
            ).all()
            for goal in goals_tomorrow:
                self.send_notification(
                    "Напоминание на завтра",
                    f"Завтра дедлайн цели: {goal.name}",
                )

            # Просроченные
            goals_overdue = self.db.query(Goal).filter(
                Goal.user_id == self.user_id,
                func.date(Goal.deadline) < today,
                Goal.status_id.in_([1, 3]),
            ).all()
            for goal in goals_overdue:
                self.send_notification(
                    "Просроченная цель!",
                    f"Просрочена цель: {goal.name}",
                    "critical",
                )

            print(
                f"[NotificationService] Проверка целей: "
                f"{len(goals_today)} сегодня, "
                f"{len(goals_tomorrow)} завтра, "
                f"{len(goals_overdue)} просрочено"
            )
        except Exception as e:
            print(f"[NotificationService] Ошибка при проверке целей: {e}")


    def check_habit_streak(self):
        """Проверить привычки и напомнить о них.

        Использует переданную сессию self.db.
        """
        try:
            from src.models.habit import Habit

            if self.user_id is None:
                return
            if self.db is None:
                print("[NotificationService] Нет сессии БД для проверки привычек")
                return

            habits = self.db.query(Habit).filter(
                Habit.user_id == self.user_id,
                Habit.status_id == 1,
            ).all()

            for habit in habits:
                if habit.type_id == 1:      # ежедневная
                    self.send_notification(
                        "Напоминание о привычке",
                        f"Не забудьте о привычке: {habit.name}",
                    )

            print(f"[NotificationService] Проверка привычек: {len(habits)} активных")
        except Exception as e:
            print(f"[NotificationService] Ошибка при проверке привычек: {e}")

    def check_scheduled_notifications(self):
        """Отправить плановые напоминания из таблицы notification_schedule.

        Окно ±5 минут вокруг текущего локального времени пользователя.check_goal_deadlines 
        После отправки помечает запись как доставленную (status_id=3)
        и планирует следующий цикл (+1 день) чтобы напоминание повторилось.
        """
        try:
            from src.models.notification import NotificationSchedule
            from src.config.database import SessionLocal

            if self.user_id is None:
                return

            now = _now_local(_get_user_timezone(self.user_id))
            t_min = now - timedelta(minutes=5)
            t_max = now + timedelta(minutes=1)

            db = SessionLocal()
            try:
                pending = db.query(NotificationSchedule).filter(
                    NotificationSchedule.user_id == self.user_id,
                    NotificationSchedule.delivery_status_id == 2,  # pending
                    NotificationSchedule.send_at.between(t_min, t_max),
                ).all()

                for n in pending:
                    sent = self.send_notification("Напоминание", n.content or "")
                    if sent:
                        n.delivery_status_id = 3  # delivered
                        # Создаём запись на следующий день (повтор)
                        next_n = NotificationSchedule(
                            user_id=n.user_id,
                            type_id=n.type_id,
                            send_at=n.send_at + timedelta(days=1),
                            content=n.content,
                            delivery_status_id=2,
                        )
                        db.add(next_n)

                if pending:
                    db.commit()
                    print(f"[NotificationService] Отправлено {len(pending)} плановых уведомлений")
            finally:
                db.close()

        except Exception as e:
            print(f"[NotificationService] Ошибка при проверке уведомлений: {e}")

    def schedule_daily_backup(self, hour: int = 2, minute: int = 0):
        """Расписание для ежедневного бэкапа в 2:00 ночи.

        Параметр `user_id` может быть передан через аргументы при добавлении задачи
        (см. вызов add_job с args).
        """
        try:
            if self._scheduler is None:
                return
            
            job_id = "daily_backup"
            # Удалить старую работу если есть
            if job_id in self._jobs:
                self._scheduler.remove_job(job_id)
            
            # Добавить новую работу
            trigger = CronTrigger(hour=hour, minute=minute)
            # По умолчанию задача запускает общий бэкап (без аргументов).
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

    def _do_backup_user(self, user_id: int = None):
        """Выполнить бэкап для конкретного пользователя (если user_id)."""
        try:
            from src.services.backup_service import BackupService
            from src.config.database import SessionLocal
            db = SessionLocal()
            service = BackupService(db)
            if user_id is not None:
                backup_file = service.create_backup(user_id=user_id)
            else:
                backup_file = service.create_backup()
            db.close()
            print(f"[BackupService] Бэкап выполнен: {backup_file}")
        except Exception as e:
            print(f"[BackupService] Ошибка при бэкапе (user): {e}")

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
            service = BackupService(db)
            backup_file = service.create_backup()
            db.close()
            print(f"[BackupService] Бэкап выполнен: {backup_file}")
        except Exception as e:
            print(f"[BackupService] Ошибка при бэкапе: {e}")

    def _get_user_settings(self) -> dict:
        """Прочитать настройки уведомлений из БД для текущего пользователя."""
        if self.user_id is None:
            return {}
        try:
            from src.models.user import User
            u = self.db.query(User).filter(User.id == self.user_id).first()
            return dict(u.settings or {}) if u else {}
        except Exception:
            return {}

    def _do_notifications(self):
        """Выполнить проверку уведомлений с учётом настроек пользователя.

        Метод вызывается APScheduler каждые N минут (без systemd-таймера),
        поэтому обязательно читает актуальные настройки из БД перед отправкой.
        """
        try:
            settings = self._get_user_settings()

            # Глобальный флаг отключения
            if not settings.get("notifications", True):
                print("[NotificationService] Уведомления отключены в настройках")
                return

            # Плановые уведомления из таблицы notification_schedule — всегда
            self.check_scheduled_notifications()

            # Уведомления о целях
            if settings.get("notif_goals", True):
                self.check_goal_deadlines()
            else:
                print("[NotificationService] Уведомления о целях отключены")

            # Уведомления о привычках
            if settings.get("notif_habits", True):
                self.check_habit_streak()
            else:
                print("[NotificationService] Уведомления о привычках отключены")

        except Exception as e:
            print(f"[NotificationService] Ошибка при проверке уведомлений: {e}")