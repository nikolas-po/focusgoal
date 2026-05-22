"""Утилиты для работы с датами"""
from datetime import datetime, date, timedelta, timezone
from typing import Optional


def now() -> datetime:
    return datetime.now()


def today() -> date:
    return datetime.now().date()


def days_until(target_date: date) -> int:
    return (target_date - today()).days


def format_date_ru(d) -> str:
    if d is None:
        return "—"
    months = [
        "января", "февраля", "марта", "апреля", "мая", "июня",
        "июля", "августа", "сентября", "октября", "ноября", "декабря",
    ]
    if isinstance(d, datetime):
        d = d.date()
    return f"{d.day} {months[d.month - 1]} {d.year}"


def format_duration(minutes: int) -> str:
    if minutes <= 0:
        return "0 мин"
    h = minutes // 60
    m = minutes % 60
    if h > 0 and m > 0:
        return f"{h}ч {m}мин"
    if h > 0:
        return f"{h}ч"
    return f"{m}мин"


def is_overdue(deadline: Optional[date]) -> bool:
    if deadline is None:
        return False
    if isinstance(deadline, datetime):
        deadline = deadline.date()
    return deadline < today()


def week_range(offset: int = 0):
    """Возвращает (start, end) для недели со смещением offset"""
    base = today()
    start = base - timedelta(days=base.weekday()) + timedelta(weeks=offset)
    end = start + timedelta(days=6)
    return start, end
