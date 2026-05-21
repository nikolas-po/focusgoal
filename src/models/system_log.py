from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from src.models.base import BaseModel
from datetime import datetime

class SystemLog(BaseModel):
    __tablename__ = "system_log"
    event_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    event_type_id = Column(Integer, ForeignKey("system_log_event_type.id"), default=3)
    message = Column(Text, nullable=False)
    context = Column(String(255), nullable=True)

    event_type = relationship("SystemLogEventType")