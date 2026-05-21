import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Константы приложения
    APP_NAME = "FocusGoal"
    APP_VERSION = "1.0.0"
    DEBUG = False
    LOG_LEVEL = "INFO"

    # Параметры БД 
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = int(os.getenv("DB_PORT")) if os.getenv("DB_PORT") else None
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")

    # Директории
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    BACKUP_DIR = Path(os.getenv("BACKUP_DIR", str(BASE_DIR / "backups")))
    LOG_DIR = BASE_DIR / "logs"

    # Безопасность
    ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
    PASSWORD_MIN_LENGTH = int(os.getenv("PASSWORD_MIN_LENGTH", "8"))
    MAX_LOGIN_ATTEMPTS = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
    LOGIN_BLOCK_TIME = int(os.getenv("LOGIN_BLOCK_TIME", "30"))

    # Резервное копирование
    BACKUP_RETENTION_DAYS = int(os.getenv("BACKUP_RETENTION_DAYS", "7"))
    AUTO_BACKUP_TIME = os.getenv("AUTO_BACKUP_TIME", "02:00")

    # Валидация
    NICKNAME_MIN_LENGTH = 3
    NICKNAME_MAX_LENGTH = 50
    GOAL_NAME_MIN_LENGTH = 3
    HABIT_NAME_MIN_LENGTH = 3
    MIN_DISK_SPACE_MB = 100

    @property
    def database_url(self) -> str:
        if not all([self.DB_HOST, self.DB_PORT, self.DB_NAME, self.DB_USER, self.DB_PASSWORD]):
            raise ValueError("Не все параметры подключения к БД заданы в .env")
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    def create_directories(self):
        self.BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        self.LOG_DIR.mkdir(parents=True, exist_ok=True)