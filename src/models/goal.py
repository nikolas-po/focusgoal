from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from src.models.base import BaseModel

class Goal(BaseModel):
    __tablename__ = "goal"
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    deadline = Column(DateTime, nullable=True)
    priority_id = Column(Integer, ForeignKey("goal_priority.id"), default=2)
    repeat_type_id = Column(Integer, ForeignKey("goal_repeat_type.id"), default=1)
    fail_behavior_id = Column(Integer, ForeignKey("goal_fail_behavior.id"), default=2)
    status_id = Column(Integer, ForeignKey("goal_status.id"), default=1)

    user = relationship("User", back_populates="goals")
    priority = relationship("GoalPriority")
    repeat_type = relationship("GoalRepeatType")
    fail_behavior = relationship("GoalFailBehavior")
    status = relationship("GoalStatus")
    sessions = relationship("FocusSession", back_populates="goal")