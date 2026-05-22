"""Конфигурация логирования"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from src.config.settings import Settings

settings = Settings()


def setup_logging() -> logging.Logger:
    """Настройка системы логирования с ротацией файлов"""
    settings.LOG_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("FocusGoal")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL, logging.INFO))

    if logger.handlers:
        logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    log_file = settings.LOG_DIR / "focusgoal.log"
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
