"""Модель журнала выполнений"""
from sqlalchemy import Column, Integer, DateTime, ForeignKey, Text, CheckConstraint
from sqlalchemy.orm import relationship
from src.models.base import BaseModel
from datetime import datetime, timezone


class CompletionLog(BaseModel):
    """Журнал истории выполнения целей и привычек"""
    __tablename__ = "completion_log"

    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    object_type_id = Column(Integer, ForeignKey("completion_object_type.id"), nullable=False)
    object_id = Column(Integer, nullable=False)
    completed_at = Column(DateTime, default=lambda: datetime.now, nullable=False)
    progress = Column(Integer, nullable=True)
    comment = Column(Text, nullable=True)

    user = relationship("User", back_populates="completion_logs")
    object_type = relationship("CompletionObjectType")

    __table_args__ = (
        CheckConstraint("progress IS NULL OR progress >= 0", name="chk_completion_progress"),
    )

    def __repr__(self):
        return f"<CompletionLog(id={self.id}, object_id={self.object_id})>"
