"""Репозиторий уведомлений"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from src.repositories.base_repository import BaseRepository
from src.models.notification import NotificationSchedule
from typing import List
from datetime import datetime


class NotificationRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(NotificationSchedule, db)

    def get_by_user(self, user_id: int) -> List[NotificationSchedule]:
        return self.db.query(NotificationSchedule).filter(
            NotificationSchedule.user_id == user_id
        ).all()

    def get_pending(self, user_id: int) -> List[NotificationSchedule]:
        return self.db.query(NotificationSchedule).filter(
            and_(
                NotificationSchedule.user_id == user_id,
                NotificationSchedule.delivery_status_id == 2,
                NotificationSchedule.send_at <= datetime.now(),
            )
        ).all()

    def mark_as_sent(self, notification_id: int) -> bool:
        n = self.get_by_id(notification_id)
        if n:
            n.delivery_status_id = 1
            self.db.commit()
            return True
        return False
