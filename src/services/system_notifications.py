"""Системные уведомления через systemd user timer (работают без запущенного приложения).

Установка: NotificationInstaller.install()
Удаление:  NotificationInstaller.uninstall()

Уведомления отправляются через notify-send и хранят расписание в БД.
"""
from __future__ import annotations
import os, sys, subprocess
from pathlib import Path


class NotificationInstaller:
    """Управление systemd user unit для уведомлений FocusGoal."""

    SERVICE_NAME = "focusgoal-notify"
    SCRIPT_NAME  = "focusgoal_notify.py"

    @classmethod
    def _systemd_dir(cls) -> Path:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        d = base / "systemd" / "user"
        d.mkdir(parents=True, exist_ok=True)
        return d

    @classmethod
    def _script_path(cls) -> Path:
        return Path(os.environ.get("XDG_DATA_HOME",
                    Path.home() / ".local" / "share")) / "focusgoal" / cls.SCRIPT_NAME

    @classmethod
    def _write_notify_script(cls):
        """Записать standalone-скрипт уведомлений."""
        script = cls._script_path()
        script.parent.mkdir(parents=True, exist_ok=True)

        # Нужно знать путь к venv/python и к проекту
        python = sys.executable
        project_root = str(Path(__file__).resolve().parent.parent.parent)

        script_text = """#!/usr/bin/env python3
# Автоматически сгенерировано FocusGoal
import sys, subprocess
sys.path.insert(0, {project_root!r})


def _notify(title: str, msg: str):
    try:
        subprocess.run(["notify-send", "-a", "FocusGoal", "-i", "dialog-information",
                       title, msg], timeout=5)
    except Exception:
        pass


def _now_for_timezone(timezone_name: str) -> datetime:
    try:
        from datetime import datetime
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo(timezone_name)).replace(tzinfo=None)
    except Exception:
        from datetime import datetime
        return datetime.now()


def main():
    try:
        from src.config.database import SessionLocal
        from src.models.user import User
        from src.models.notification_schedule import NotificationSchedule
        from src.models.goal import Goal
        from datetime import datetime, timedelta

        db = SessionLocal()
        users = db.query(User).all()
        for user in users:
            tz = user.timezone or "Europe/Moscow"
            now = _now_for_timezone(tz)
            window_start = now - timedelta(minutes=5)
            pending = db.query(NotificationSchedule).filter(
                NotificationSchedule.user_id == user.id,
                NotificationSchedule.status_id == 2,  # PENDING
                NotificationSchedule.send_at >= window_start,
                NotificationSchedule.send_at <= now + timedelta(minutes=1),
            ).all()
            for n in pending:
                _notify("FocusGoal", n.content or "Напоминание")
                n.status_id = 1  # SENT

            today_end = now.replace(hour=23, minute=59, second=59)
            today_start = now.replace(hour=0, minute=0, second=0)
            goals_due = db.query(Goal).filter(
                Goal.user_id == user.id,
                Goal.deadline >= today_start,
                Goal.deadline <= today_end,
                Goal.status_id == 1,
            ).all()
            for g in goals_due:
                _notify("Срок выполнения цели", f"Сегодня нужно выполнить: «{{g.name}}»")

        db.commit()
        db.close()
    except Exception as e:
        import logging
        logging.getLogger("focusgoal_notify").error(str(e))

if __name__ == "__main__":
    main()
""".format(project_root=project_root)
        script.write_text(script_text, encoding="utf-8")
        script.chmod(0o755)
        return script

    @classmethod
    def install(cls) -> bool:
        """Установить systemd user timer. Вызвать один раз после регистрации."""
        try:
            script = cls._write_notify_script()
            sdir = cls._systemd_dir()
            python = sys.executable

            # .service
            (sdir / f"{cls.SERVICE_NAME}.service").write_text(
                f"""[Unit]
Description=FocusGoal — уведомления о целях и привычках
After=graphical-session.target

[Service]
Type=oneshot
ExecStart={python} {script}
Environment=DISPLAY=:0
""", encoding="utf-8")

            # .timer (каждые 5 минут)
            (sdir / f"{cls.SERVICE_NAME}.timer").write_text(
                f"""[Unit]
Description=FocusGoal — таймер уведомлений

[Timer]
OnBootSec=1min
OnUnitActiveSec=5min
AccuracySec=30s

[Install]
WantedBy=timers.target
""", encoding="utf-8")

            subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
            subprocess.run(["systemctl", "--user", "enable", "--now",
                           f"{cls.SERVICE_NAME}.timer"], check=True)
            return True
        except Exception as e:
            import logging
            logging.getLogger("FocusGoal").warning(f"Systemd timer install failed: {e}")
            return False

    @classmethod
    def uninstall(cls) -> bool:
        """Удалить systemd user timer."""
        try:
            subprocess.run(["systemctl", "--user", "disable", "--now",
                           f"{cls.SERVICE_NAME}.timer"], check=False)
            for ext in (".service", ".timer"):
                f = cls._systemd_dir() / f"{cls.SERVICE_NAME}{ext}"
                if f.exists(): f.unlink()
            subprocess.run(["systemctl", "--user", "daemon-reload"], check=False)
            cls._script_path().unlink(missing_ok=True)
            return True
        except Exception:
            return False

    @classmethod
    def is_installed(cls) -> bool:
        try:
            r = subprocess.run(
                ["systemctl", "--user", "is-active", f"{cls.SERVICE_NAME}.timer"],
                capture_output=True, text=True)
            return r.returncode == 0
        except Exception:
            return False
