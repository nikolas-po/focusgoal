"""Репозиторий системного лога"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from src.repositories.base_repository import BaseRepository
from src.models.system_log import SystemLog
from typing import List
from datetime import datetime, timedelta


class SystemLogRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(SystemLog, db)

    def get_recent(self, days: int = 30, context: str = None) -> List[SystemLog]:
        start_date = datetime.now() - timedelta(days=days)
        query = self.db.query(SystemLog).filter(SystemLog.event_at >= start_date)
        if context:
            query = query.filter(SystemLog.context == context)
        return query.order_by(SystemLog.event_at.desc()).all()

    def log_event(self, event_type_id: int, message: str, context: str = None) -> SystemLog:
        return self.create(
            event_type_id=event_type_id,
            message=message,
            context=context,
        )
