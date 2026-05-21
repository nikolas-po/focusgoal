from sqlalchemy import Column, SmallInteger, String, Boolean
from src.models.base import Base

class SystemLogEventType(Base):
    __tablename__ = "system_log_event_type"
    id = Column(SmallInteger, primary_key=True, autoincrement=False)
    code = Column(String(30), unique=True, nullable=False)
    name_ru = Column(String(100), nullable=False)
    sort_order = Column(SmallInteger, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)