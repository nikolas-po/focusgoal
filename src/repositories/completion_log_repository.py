"""Репозиторий журнала выполнений"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from src.repositories.base_repository import BaseRepository
from src.models.completion_log import CompletionLog
from typing import List
from datetime import datetime, timedelta


class CompletionLogRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(CompletionLog, db)

    def get_by_user(self, user_id: int, days: int = 30) -> List[CompletionLog]:
        start_date = datetime.now() - timedelta(days=days)
        return self.db.query(CompletionLog).filter(
            and_(
                CompletionLog.user_id == user_id,
                CompletionLog.completed_at >= start_date,
            )
        ).order_by(CompletionLog.completed_at.desc()).all()

    def get_by_object(self, object_type_id: int, object_id: int) -> List[CompletionLog]:
        return self.db.query(CompletionLog).filter(
            and_(
                CompletionLog.object_type_id == object_type_id,
                CompletionLog.object_id == object_id,
            )
        ).order_by(CompletionLog.completed_at.desc()).all()

    def get_completion_count(self, user_id: int, object_type_id: int,
                              object_id: int, days: int = 1) -> int:
        start_date = datetime.now() - timedelta(days=days)
        count = self.db.query(func.count(CompletionLog.id)).filter(
            and_(
                CompletionLog.user_id == user_id,
                CompletionLog.object_type_id == object_type_id,
                CompletionLog.object_id == object_id,
                CompletionLog.completed_at >= start_date,
            )
        ).scalar()
        return count or 0
