"""Репозиторий целей (ТЗ FR-002)"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from src.repositories.base_repository import BaseRepository
from src.models.goal import Goal
from typing import List, Optional, Dict


class GoalRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(Goal, db)

    def get_by_user(self, user_id: int, filters: Dict = None) -> List[Goal]:
        query = self.db.query(Goal).filter(Goal.user_id == user_id)
        if filters:
            if "status_id" in filters:
                query = query.filter(Goal.status_id == filters["status_id"])
            if "priority_id" in filters:
                query = query.filter(Goal.priority_id == filters["priority_id"])
        return query.order_by(Goal.created_at.desc()).all()

    def get_active_goals(self, user_id: int) -> List[Goal]:
        return self.db.query(Goal).filter(
            and_(Goal.user_id == user_id, Goal.status_id == 1)
        ).all()

    def soft_delete(self, goal_id: int, user_id: int) -> bool:
        goal = self.db.query(Goal).filter(
            and_(Goal.id == goal_id, Goal.user_id == user_id)
        ).first()
        if goal:
            goal.status_id = 5  # DELETED
            self.db.commit()
            return True
        return False

    def count_by_status(self, user_id: int, status_id: int) -> int:
        return self.db.query(Goal).filter(
            and_(Goal.user_id == user_id, Goal.status_id == status_id)
        ).count()
