from sqlalchemy import Column, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from src.models.base import BaseModel
from datetime import datetime, timezone

class CompletionLog(BaseModel):
    __tablename__ = "completion_log"
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    object_type_id = Column(Integer, ForeignKey("completion_object_type.id"), nullable=False)
    object_id = Column(Integer, nullable=False)
    completed_at = Column(DateTime, default=lambda: datetime.now, nullable=False)
    progress = Column(Integer, nullable=True)
    comment = Column(Text, nullable=True)

    user = relationship("User", back_populates="completion_logs")
    object_type = relationship("CompletionObjectType")