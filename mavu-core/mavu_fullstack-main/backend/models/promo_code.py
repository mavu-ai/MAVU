from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class PromoCode(TimestampMixin, Base):
    """
    Model for storing promotional codes and their activation status.

    Attributes:
        id: Unique identifier for the promo code
        code: The promotional code string (unique)
        is_active: Whether the promo code is currently active
        user_id: ID of the user who activated this code (nullable)
        activated_at: Timestamp when the code was activated
        created_at: Timestamp when code was created (from TimestampMixin)
        updated_at: Timestamp when code was last updated (from TimestampMixin)

    Relationships:
        user: The user who activated this promo code (if activated)
    """
    __tablename__ = "promo_codes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    activated_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="promo_codes")
