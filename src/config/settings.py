"""Настройки приложения FocusGoal"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class Settings:
    APP_NAME = os.getenv("APP_NAME", "FocusGoal")
    APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "5432"))
    DB_NAME = os.getenv("DB_NAME", "")
    DB_USER = os.getenv("DB_USER", "")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")

    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    BACKUP_DIR = Path(os.getenv("BACKUP_DIR", str(Path(__file__).resolve().parent.parent.parent / "backups")))
    LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"

    ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "")
    PASSWORD_MIN_LENGTH = int(os.getenv("PASSWORD_MIN_LENGTH", "8"))
    MAX_LOGIN_ATTEMPTS = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
    LOGIN_BLOCK_TIME = int(os.getenv("LOGIN_BLOCK_TIME", "30"))

    BACKUP_RETENTION_DAYS = int(os.getenv("BACKUP_RETENTION_DAYS", "7"))
    AUTO_BACKUP_TIME = os.getenv("AUTO_BACKUP_TIME", "02:00")

    FOCUS_SESSIONS = [25, 50, 90]
    EMERGENCY_EXIT_HOTKEY = "Ctrl+Shift+Esc"

    NICKNAME_MIN_LENGTH = 3
    NICKNAME_MAX_LENGTH = 20
    MIN_DISK_SPACE_MB = int(os.getenv("MIN_DISK_SPACE_MB", "100"))

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    def create_directories(self):
        self.BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        self.LOG_DIR.mkdir(parents=True, exist_ok=True)
