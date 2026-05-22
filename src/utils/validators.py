"""Валидаторы входных данных"""
import re
from src.config.settings import Settings

settings = Settings()


def validate_email(email: str) -> bool:
    if not email:
        return False
    pattern = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email.strip()))


def validate_password(password: str) -> bool:
    if not password:
        return False
    if len(password) < settings.PASSWORD_MIN_LENGTH:
        return False
    if not any(c.isalpha() for c in password):
        return False
    if not any(c.isdigit() for c in password):
        return False
    return True


def validate_nickname(nickname: str) -> bool:
    if not nickname:
        return False
    n = nickname.strip()
    return settings.NICKNAME_MIN_LENGTH <= len(n) <= settings.NICKNAME_MAX_LENGTH


def validate_goal_name(name: str) -> bool:
    return bool(name and len(name.strip()) >= settings.GOAL_NAME_MIN_LENGTH)


def validate_habit_name(name: str) -> bool:
    return bool(name and len(name.strip()) >= settings.HABIT_NAME_MIN_LENGTH)
