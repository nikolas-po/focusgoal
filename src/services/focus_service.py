"""Сервис фокус-сессий (ТЗ FR-009)"""
import psutil
from sqlalchemy.orm import Session
from src.repositories.session_repository import SessionRepository
from src.models.focus_session import FocusSession
from typing import Optional, List, Dict
from datetime import datetime


class FocusService:
    def __init__(self, db: Session):
        self.db = db
        self.session_repo = SessionRepository(db)

    def get_running_processes(self) -> List[Dict]:
        """Получить список запущенных процессов через psutil"""
        processes = []
        for proc in psutil.process_iter(["pid", "name", "exe"]):
            try:
                processes.append({
                    "pid": proc.info["pid"],
                    "name": proc.info["name"],
                    "exe": proc.info.get("exe", ""),
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return processes

    def start_session(self, user_id: int, duration: int,
                      goal_id: int = None) -> FocusSession:
        return self.session_repo.create(
            user_id=user_id,
            goal_id=goal_id,
            start_time=datetime.now(),
            planned_duration=duration,
            status_id=1,
            blocked_apps_count=0,
            blocked_processes_list=[],
        )

    def stop_session(self, session_id: int,
                     status_id: int = 2) -> Optional[FocusSession]:
        """Завершить сессию, записать фактическую длительность"""
        session = self.session_repo.get_by_id(session_id)
        if session:
            elapsed = int((datetime.now() - session.start_time).total_seconds() / 60)
            session.actual_duration = elapsed
            session.status_id = status_id
            self.db.commit()
            self.db.refresh(session)
        return session

    def get_sessions(self, user_id: int) -> List[FocusSession]:
        return self.session_repo.get_by_user(user_id)
