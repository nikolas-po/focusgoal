from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from src.models.base import BaseModel

class FocusSession(BaseModel):
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