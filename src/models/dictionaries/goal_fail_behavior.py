"""Справочник: GoalFailBehavior"""
from sqlalchemy import Column, SmallInteger, String, Boolean
from src.models.base import Base


class GoalFailBehavior(Base):
    __tablename__ = "goal_fail_behavior"

    # autoincrement=False — запрет GENERATED ALWAYS AS IDENTITY в PostgreSQL,
    # чтобы можно было явно вставлять id при заполнении справочника
    id        = Column(SmallInteger, primary_key=True, autoincrement=False)
    code      = Column(String(30),  unique=True, nullable=False)
    name_ru   = Column(String(100), nullable=False)
    sort_order = Column(SmallInteger, default=0, nullable=False)
    is_active  = Column(Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<GoalFailBehavior({self.id}, {self.code})>"
