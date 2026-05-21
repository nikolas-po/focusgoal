from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.orm import relationship
from src.models.base import BaseModel
from datetime import datetime, timezone

class User(BaseModel):
    __tablename__ = "user"
    nickname = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=True)
    password_hash = Column(String(255), nullable=False)
    registered_at = Column(DateTime, default=lambda: datetime.now, nullable=False)
    timezone = Column(String(50), default="Europe/Moscow", nullable=False)
    settings = Column(JSON, default=dict)
    local_data_path = Column(String(255), nullable=True)
    gdpr_consent = Column(DateTime, nullable=True)

    goals = relationship("Goal", back_populates="user", cascade="all, delete-orphan")
    habits = relationship("Habit", back_populates="user", cascade="all, delete-orphan")
    focus_sessions = relationship("FocusSession", back_populates="user", cascade="all, delete-orphan")
    blocked_apps = relationship("BlockedApp", back_populates="user", cascade="all, delete-orphan")
    completion_logs = relationship("CompletionLog", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("NotificationSchedule", back_populates="user", cascade="all, delete-orphan")