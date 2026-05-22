"""Сервис управления привычками (ТЗ FR-003)"""
from sqlalchemy.orm import Session
from src.repositories.habit_repository import HabitRepository
from src.models.habit import Habit
from src.models.completion_log import CompletionLog
from typing import List, Optional, Dict
from datetime import datetime, date, timezone


class HabitService:
    def __init__(self, db: Session):
        self.db = db
        self.habit_repo = HabitRepository(db)

    def create_habit(self, user_id: int, data: Dict) -> Habit:
        data["user_id"] = user_id
        data.setdefault("start_date", date.today())
        data.setdefault("status_id", 1)
        data.setdefault("current_streak", 0)
        data.setdefault("max_streak", 0)
        return self.habit_repo.create(**data)

    def get_habits(self, user_id: int) -> List[Habit]:
        return self.habit_repo.get_by_user(user_id)

    def update_habit(self, habit_id: int, user_id: int, data: Dict) -> Optional[Habit]:
        habit = self.habit_repo.get_by_id(habit_id)
        if habit and habit.user_id == user_id:
            return self.habit_repo.update(habit_id, **data)
        return None

    def mark_completed(self, habit_id: int, user_id: int,
                       progress: int = None) -> Optional[Habit]:
        """Отметить выполнение, обновить серию, записать в журнал"""
        habit = self.habit_repo.get_by_id(habit_id)
        if not habit or habit.user_id != user_id:
            return None

        habit.current_streak += 1
        habit.max_streak = max(habit.max_streak, habit.current_streak)
        habit.last_completed_at = datetime.now()

        log = CompletionLog(
            user_id=user_id,
            object_type_id=2,
            object_id=habit_id,
            completed_at=datetime.now(),
            progress=progress,
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(habit)
        return habit

    def delete_habit(self, habit_id: int, user_id: int) -> bool:
        habit = self.habit_repo.get_by_id(habit_id)
        if habit and habit.user_id == user_id:
            self.habit_repo.update(habit_id, status_id=4)
            return True
        return False

    def archive_habit(self, habit_id: int, user_id: int) -> bool:
        habit = self.habit_repo.get_by_id(habit_id)
        if habit and habit.user_id == user_id:
            self.habit_repo.update(habit_id, status_id=2)
            return True
        return False
