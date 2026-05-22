"""Модель фокус-сессии"""
from sqlalchemy import Column, Integer, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from src.models.base import BaseModel


class FocusSession(BaseModel):
    """История сессий продуктивности"""
    __tablename__ = "focus_session"

    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    goal_id = Column(Integer, ForeignKey("goal.id", ondelete="SET NULL"), nullable=True)
    start_time = Column(DateTime, nullable=False)
    planned_duration = Column(Integer, nullable=False)
    actual_duration = Column(Integer, nullable=True)
    status_id = Column(Integer, ForeignKey("focus_session_status.id"), default=1)
    blocked_apps_count = Column(Integer, default=0, nullable=False)
    blocked_processes_list = Column(JSONB, default=list)

    user = relationship("User", back_populates="focus_sessions")
    goal = relationship("Goal", back_populates="sessions")
    status = relationship("FocusSessionStatus")

    __table_args__ = (
        CheckConstraint("planned_duration > 0", name="chk_session_duration"),
        CheckConstraint("planned_duration <= 480", name="chk_session_planned_max"),
    )

    def __repr__(self):
        return f"<FocusSession(id={self.id}, duration={self.planned_duration}min)>"
