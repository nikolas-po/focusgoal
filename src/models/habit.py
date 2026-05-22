"""Модель привычки"""
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from src.models.base import BaseModel
from datetime import date


class Habit(BaseModel):
    """Таблица привычек для отслеживания"""
    __tablename__ = "habit"

    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    type_id = Column(Integer, ForeignKey("habit_type.id"), default=1)
    mode_id = Column(Integer, ForeignKey("habit_mode.id"), default=1)
    status_id = Column(Integer, ForeignKey("habit_status.id"), default=1)
    target_value = Column(Integer, nullable=True)
    current_streak = Column(Integer, default=0, nullable=False)
    max_streak = Column(Integer, default=0, nullable=False)
    start_date = Column(Date, nullable=False, default=date.today)
    last_completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="habits")
    type = relationship("HabitType")
    mode = relationship("HabitMode")
    status = relationship("HabitStatus")

    __table_args__ = (
        CheckConstraint("length(trim(name)) >= 3", name="chk_habit_name_length"),
        CheckConstraint("current_streak >= 0 AND max_streak >= 0", name="chk_habit_streak"),
    )

    def __repr__(self):
        return f"<Habit(id={self.id}, name=\'{self.name}\', streak={self.current_streak})>"
