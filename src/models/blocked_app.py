"""Модель заблокированного приложения"""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from src.models.base import BaseModel


class BlockedApp(BaseModel):
    """Индивидуальные настройки блокировки приложений"""
    __tablename__ = "blocked_app"

    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    app_name = Column(String(100), nullable=False)
    process_name = Column(String(255), nullable=False)
    block_level_id = Column(Integer, ForeignKey("block_level.id"), default=1)
    block_time_limit = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    user = relationship("User", back_populates="blocked_apps")
    block_level = relationship("BlockLevel")

    __table_args__ = (
        CheckConstraint("length(trim(app_name)) >= 2", name="chk_blocked_app_name_length"),
    )

    def __repr__(self):
        return f"<BlockedApp(id={self.id}, name=\'{self.app_name}\')>"
