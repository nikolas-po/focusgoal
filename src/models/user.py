"""Модель пользователя"""
from sqlalchemy import Column, Integer, String, DateTime, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from src.models.base import BaseModel
from datetime import datetime, timezone


class User(BaseModel):
    """Таблица пользователей FocusGoal"""
    __tablename__ = "user"

    nickname        = Column(String(50),  unique=True, nullable=False)
    email           = Column(String(255), unique=True, nullable=True)
    password_hash   = Column(String(255), nullable=False)
    registered_at   = Column(DateTime, default=lambda: datetime.now(), nullable=False)
    timezone        = Column(String(50), default="Europe/Moscow", nullable=False)
    settings        = Column(JSONB, default=dict)
    local_data_path = Column(String(255), nullable=True)

    goals           = relationship("Goal",                 back_populates="user", cascade="all, delete-orphan")
    habits          = relationship("Habit",                back_populates="user", cascade="all, delete-orphan")
    focus_sessions  = relationship("FocusSession",         back_populates="user", cascade="all, delete-orphan")
    blocked_apps    = relationship("BlockedApp",           back_populates="user", cascade="all, delete-orphan")
    completion_logs = relationship("CompletionLog",        back_populates="user", cascade="all, delete-orphan")
    notifications   = relationship("NotificationSchedule", back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(
            "length(trim(nickname)) >= 3 AND length(trim(nickname)) <= 50",
            name="chk_user_nickname_length",
        ),
        CheckConstraint(
            "length(password_hash) >= 60",
            name="chk_user_password_hash_length",
        ),
    )

    def __repr__(self):
        return f"<User(id={self.id}, nickname=\'{self.nickname}\')>"
