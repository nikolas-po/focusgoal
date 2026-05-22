"""Репозиторий привычек (ТЗ FR-003)"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from src.repositories.base_repository import BaseRepository
from src.models.habit import Habit
from typing import List


class HabitRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(Habit, db)

    def get_by_user(self, user_id: int) -> List[Habit]:
        return self.db.query(Habit).filter(
            Habit.user_id == user_id
        ).order_by(Habit.created_at.desc()).all()

    def get_active_habits(self, user_id: int) -> List[Habit]:
        return self.db.query(Habit).filter(
            and_(Habit.user_id == user_id, Habit.status_id == 1)
        ).all()
