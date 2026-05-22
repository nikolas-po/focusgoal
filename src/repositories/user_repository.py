"""Репозиторий пользователей"""
from sqlalchemy.orm import Session
from src.repositories.base_repository import BaseRepository
from src.models.user import User
from typing import Optional


class UserRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(User, db)

    def get_by_nickname(self, nickname: str) -> Optional[User]:
        return self.db.query(User).filter(User.nickname == nickname).first()

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def nickname_exists(self, nickname: str) -> bool:
        return self.db.query(User).filter(User.nickname == nickname).count() > 0

    def email_exists(self, email: str) -> bool:
        return self.db.query(User).filter(User.email == email).count() > 0
