from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class FCMDevice(TimestampMixin, Base):
    """
    Model for storing Firebase Cloud Messaging (FCM) device registrations.

    Attributes:
        id: Unique identifier for the device registration
        device_id: Unique device identifier (UUID from app)
        registration_id: FCM registration token for push notifications
        language: Device language preference (default: 'en')
        device_type: Type of device ('ios', 'android', 'web')
        user_id: ID of the user who owns this device
        created_at: Timestamp when device was registered (from TimestampMixin)
        updated_at: Timestamp when device was last updated (from TimestampMixin)

    Relationships:
        user: The user who owns this device
    """

    __tablename__ = "fcm_devices"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, unique=True, index=True, nullable=False)
    registration_id = Column(String, nullable=False)
    language = Column(String, default="en", nullable=False)
    device_type = Column(String, nullable=False)  # 'ios', 'android', 'web'
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    user = relationship("User", back_populates="fcm_devices")
