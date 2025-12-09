from sqlalchemy import BigInteger, Boolean, Column, Integer, String, Time
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class User(TimestampMixin, Base):
    """
    Model for storing user account information and profile data.

    Supports both mobile app users and Telegram bot users.

    Attributes:
        id: Unique identifier for the user (primary key)
        telegram_id: Telegram user ID (for bot users, unique, optional)
        email: User's email address (unique, optional)
        username: User's username (unique, optional)
        name: User's real name (extracted from conversation, nullable for guest users)
        age: User's age (extracted from conversation, nullable for guest users)
        gender: User's gender (extracted from conversation, nullable for guest users)
        language: Preferred language (default: 'en')
        skin_id: Selected character skin ID (default: 1)
        night_mode: Whether night mode is enabled
        night_mode_start: Start time for night mode
        night_mode_end: End time for night mode
        ui_mode: UI theme mode - "light", "dark", or "system" (default: "system")
        is_active: Whether the account is active
        is_verified: Whether the email is verified
        is_admin: Whether the user has admin privileges
        password_hash: Hashed password for authentication
        created_at: Timestamp when user was created (from TimestampMixin)
        updated_at: Timestamp when user was last updated (from TimestampMixin)

    Note:
        Guest users are identified by having null/None values for name, age, and gender.
        At least one of telegram_id or email must be set to identify the user.

    Relationships:
        chats: All chat messages from this user
        threats: Any detected threats for this user
        promo_codes: Promo codes associated with this user
        sessions: Active sessions for this user
        fcm_devices: Push notification devices
        email_verifications: Email verification records
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    # Removed user_id field - use id, telegram_id, or email as identifiers
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=True)  # For Telegram bot users
    email = Column(String, unique=True, index=True, nullable=True)
    username = Column(String, unique=True, index=True, nullable=True)
    # Guest user identification: name=None, age=None, gender=None
    name = Column(String, nullable=True)
    age = Column(Integer, nullable=True)
    gender = Column(String, nullable=True)  # No default - must be extracted from conversation
    language = Column(String, default="en", nullable=False)
    skin_id = Column(Integer, default=1, nullable=False)  # Selected character skin
    night_mode = Column(Boolean, default=False, nullable=False)
    night_mode_start = Column(Time, nullable=True)
    night_mode_end = Column(Time, nullable=True)
    ui_mode = Column(String, default="system", nullable=False)  # UI theme mode: "light", "dark", "system"
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    password_hash = Column(String, nullable=True)

    @property
    def is_guest(self) -> bool:
        """Check if user is a guest (no profile information)."""
        return self.name is None and self.age is None and self.gender is None

    @property
    def is_registered(self) -> bool:
        """Check if user has completed profile information."""
        return self.name is not None or self.age is not None or self.gender is not None

    # Relationships
    chats = relationship("Chat", back_populates="user", order_by="Chat.created_at")
    threats = relationship("Threat", back_populates="user", order_by="Threat.created_at")
    promo_codes = relationship("PromoCode", back_populates="user")
    sessions = relationship("Session", back_populates="user", order_by="Session.created_at")
    fcm_devices = relationship("FCMDevice", back_populates="user", order_by="FCMDevice.created_at")
    email_verifications = relationship("EmailVerification", back_populates="user", order_by="EmailVerification.created_at")
