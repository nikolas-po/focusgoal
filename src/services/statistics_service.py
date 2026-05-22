"""Сервис статистики и аналитики (ТЗ FR-005, FR-007)"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta, timezone
from typing import Dict, List


class StatisticsService:
    def __init__(self, db: Session):
        self.db = db

    def get_dashboard_statistics(self, user_id: int) -> Dict:
        from src.models.goal import Goal
        from src.models.habit import Habit
        from src.models.focus_session import FocusSession

        goals_total = self.db.query(func.count(Goal.id)).filter(
            Goal.user_id == user_id
        ).scalar() or 0
        goals_completed = self.db.query(func.count(Goal.id)).filter(
            and_(Goal.user_id == user_id, Goal.status_id == 2)
        ).scalar() or 0
        goals_active = self.db.query(func.count(Goal.id)).filter(
            and_(Goal.user_id == user_id, Goal.status_id == 1)
        ).scalar() or 0

        habits_total = self.db.query(func.count(Habit.id)).filter(
            Habit.user_id == user_id
        ).scalar() or 0
        habits_active = self.db.query(func.count(Habit.id)).filter(
            and_(Habit.user_id == user_id, Habit.status_id == 1)
        ).scalar() or 0

        focus_minutes = self.db.query(func.sum(FocusSession.actual_duration)).filter(
            and_(FocusSession.user_id == user_id, FocusSession.status_id == 1)
        ).scalar() or 0
        focus_sessions = self.db.query(func.count(FocusSession.id)).filter(
            FocusSession.user_id == user_id
        ).scalar() or 0

        rate = (goals_completed / goals_total * 100) if goals_total > 0 else 0.0

        return {
            "goals": {
                "total": goals_total,
                "completed": goals_completed,
                "active": goals_active,
                "rate": rate,
            },
            "habits": {"total": habits_total, "active": habits_active},
            "focus": {
                "total_minutes": int(focus_minutes),
                "sessions_total": focus_sessions,
            },
        }

    def get_goals_by_period(self, user_id: int, days: int = 30) -> List[Dict]:
        from src.models.goal import Goal

        start_date = datetime.now() - timedelta(days=days)
        results = self.db.query(
            func.date_trunc("day", Goal.created_at).label("date"),
            func.count(Goal.id).label("count"),
        ).filter(
            and_(Goal.user_id == user_id, Goal.created_at >= start_date)
        ).group_by("date").order_by("date").all()
        return [{"date": str(r.date), "count": r.count} for r in results]

    def get_habits_by_period(self, user_id: int, days: int = 30) -> List[Dict]:
        from src.models.completion_log import CompletionLog

        start_date = datetime.now() - timedelta(days=days)
        results = self.db.query(
            func.date_trunc("day", CompletionLog.completed_at).label("date"),
            func.count(CompletionLog.id).label("count"),
        ).filter(
            and_(
                CompletionLog.user_id == user_id,
                CompletionLog.object_type_id == 2,
                CompletionLog.completed_at >= start_date,
            )
        ).group_by("date").order_by("date").all()
        return [{"date": str(r.date), "count": r.count} for r in results]

    def get_focus_status_distribution(self, user_id: int) -> Dict:
        from src.models.focus_session import FocusSession

        def _count(status_id):
            return self.db.query(func.count(FocusSession.id)).filter(
                and_(FocusSession.user_id == user_id, FocusSession.status_id == status_id)
            ).scalar() or 0

        return {
            "completed": _count(1),
            "cancelled": _count(2),
            "interrupted": _count(3),
        }

    def get_heatmap_data(self, user_id: int) -> Dict:
        """Тепловая карта выполнения привычек за 12 недель"""
        from src.models.completion_log import CompletionLog

        today = datetime.now().date()
        start = today - timedelta(weeks=12)

        logs = self.db.query(CompletionLog).filter(
            and_(
                CompletionLog.user_id == user_id,
                CompletionLog.object_type_id == 2,
                CompletionLog.completed_at >= datetime.combine(
                    start, datetime.min.time()
                ),
            )
        ).all()

        result = {}
        for log in logs:
            log_date = (log.completed_at.date()
                        if hasattr(log.completed_at, "date")
                        else log.completed_at)
            delta = (log_date - start).days
            if delta < 0:
                continue
            week = delta // 7
            day = delta % 7
            key = f"{week}_{day}"
            result[key] = result.get(key, 0) + 1
        return result
