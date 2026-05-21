from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from src.models.base import BaseModel

class NotificationSchedule(BaseModel):
    __tablename__ = "notification_schedule"
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    type_id = Column(Integer, ForeignKey("notification_type.id"), default=1)
    send_at = Column(DateTime, nullable=False)
    delivery_status_id = Column(Integer, ForeignKey("notification_delivery_status.id"), default=2)
    content = Column(Text, nullable=False)

    user = relationship("User", back_populates="notifications")
    type = relationship("NotificationType")
    delivery_status = relationship("NotificationDeliveryStatus")