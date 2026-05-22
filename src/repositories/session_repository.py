"""Репозиторий фокус-сессий"""
from sqlalchemy.orm import Session
from src.repositories.base_repository import BaseRepository
from src.models.focus_session import FocusSession
from typing import List


class SessionRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(FocusSession, db)

    def get_by_user(self, user_id: int) -> List[FocusSession]:
        return self.db.query(FocusSession).filter(
            FocusSession.user_id == user_id
        ).order_by(FocusSession.start_time.desc()).all()
