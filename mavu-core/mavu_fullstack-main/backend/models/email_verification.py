from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class EmailVerification(TimestampMixin, Base):
    """
    Model for storing email verification tokens and status.

    Attributes:
        id: Unique identifier for the verification record
        user_id: ID of the user verifying their email
        email: The email address to be verified
        token: Unique verification token sent to the email
        is_verified: Whether the email has been verified
        expires_at: When the verification token expires
        verified_at: Timestamp when email was verified
        created_at: Timestamp when verification was created (from TimestampMixin)
        updated_at: Timestamp when verification was last updated (from TimestampMixin)

    Relationships:
        user: The user who is verifying their email
    """
    __tablename__ = "email_verifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    email = Column(String, nullable=False)  # The new email to be verified
    token = Column(String, unique=True, nullable=False, index=True)
    is_verified = Column(Boolean, default=False, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="email_verifications")

    def is_expired(self) -> bool:
        """Check if the verification token has expired"""
        return datetime.now(timezone.utc) > self.expires_at

    def mark_as_verified(self):
        """Mark the email as verified"""
        self.is_verified = True
        self.verified_at = datetime.now(timezone.utc)
