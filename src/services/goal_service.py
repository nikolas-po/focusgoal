"""Сервис управления целями (ТЗ FR-002)"""
from sqlalchemy.orm import Session
from src.repositories.goal_repository import GoalRepository
from src.models.goal import Goal
from src.models.completion_log import CompletionLog
from typing import List, Dict, Optional
from datetime import datetime, timezone


class GoalService:
    def __init__(self, db: Session):
        self.db = db
        self.goal_repo = GoalRepository(db)

    def create_goal(self, user_id: int, data: Dict) -> Goal:
        data["user_id"] = user_id
        # Валидация описания
        desc = (data.get("description") or "").strip()
        if desc and len(desc) < 10:
            raise ValueError("Описание цели должно быть минимум 10 символов")
        return self.goal_repo.create(**data)

    def get_goals(self, user_id: int, filters: Dict = None) -> List[Goal]:
        return self.goal_repo.get_by_user(user_id, filters)

    def update_goal(self, goal_id: int, user_id: int, data: Dict) -> Optional[Goal]:
        goal = self.goal_repo.get_by_id(goal_id)
        if goal and goal.user_id == user_id:
            desc = data.get("description")
            if desc is not None and desc.strip() and len(desc.strip()) < 10:
                raise ValueError("Описание цели должно быть минимум 10 символов")
            return self.goal_repo.update(goal_id, **data)
        return None

    def delete_goal(self, goal_id: int, user_id: int) -> bool:
        return self.goal_repo.soft_delete(goal_id, user_id)

    def complete_goal(self, goal_id: int, user_id: int) -> Optional[Goal]:
        """Отметить цель выполненной, записать в журнал"""
        goal = self.goal_repo.get_by_id(goal_id)
        if goal and goal.user_id == user_id and goal.status_id == 1:
            updated = self.goal_repo.update(goal_id, status_id=2)
            log = CompletionLog(
                user_id=user_id,
                object_type_id=1,
                object_id=goal_id,
                completed_at=datetime.now(),
            )
            self.db.add(log)
            self.db.commit()
            return updated
        return None

    def archive_goal(self, goal_id: int, user_id: int) -> Optional[Goal]:
        goal = self.goal_repo.get_by_id(goal_id)
        if goal and goal.user_id == user_id:
            return self.goal_repo.update(goal_id, status_id=6)
        return None
