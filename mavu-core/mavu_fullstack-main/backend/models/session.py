from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Boolean
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class Session(TimestampMixin, Base):
    """
    Model for storing user authentication sessions.

    Attributes:
        id: Unique identifier for the session
        user_id: ID of the user who owns this session
        session_token: Unique token for session authentication
        is_active: Whether the session is currently active
        expires_at: When the session expires (optional)
        ip_address: IP address from which session was created
        user_agent: Browser/app user agent string
        created_at: Timestamp when session was created (from TimestampMixin)
        updated_at: Timestamp when session was last updated (from TimestampMixin)

    Relationships:
        user: The user who owns this session
    """
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_token = Column(String, unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at: Optional[datetime] = Column(DateTime(timezone=True), nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)

    # Relationships
    user = relationship("User", back_populates="sessions")
