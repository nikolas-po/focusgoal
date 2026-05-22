"""Репозиторий чёрного списка приложений"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from src.repositories.base_repository import BaseRepository
from src.models.blocked_app import BlockedApp
from typing import List


class BlockedAppRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(BlockedApp, db)

    def get_by_user(self, user_id: int) -> List[BlockedApp]:
        return self.db.query(BlockedApp).filter(
            and_(BlockedApp.user_id == user_id, BlockedApp.is_active == True)
        ).all()

    def deactivate(self, blocked_app_id: int, user_id: int) -> bool:
        app = self.db.query(BlockedApp).filter(
            and_(BlockedApp.id == blocked_app_id, BlockedApp.user_id == user_id)
        ).first()
        if app:
            app.is_active = False
            self.db.commit()
            return True
        return False
