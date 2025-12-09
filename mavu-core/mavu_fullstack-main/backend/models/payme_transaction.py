from enum import IntEnum
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class TransactionStatus(IntEnum):
    """Transaction status enumeration"""
    CREATED = 1  # Transaction successfully created, waiting for confirmation
    CONFIRMED = 2  # Transaction successfully confirmed
    CANCELED_BEFORE_CONFIRM = -1  # Transaction canceled before confirmation
    CANCELED_AFTER_CONFIRM = -2  # Transaction canceled after confirmation

    @classmethod
    def choices(cls):
        return [(item.value, item.name) for item in cls]


class TransactionReason(IntEnum):
    """Transaction cancellation reason enumeration"""
    RECIPIENT_NOT_FOUND = 1  # One or more recipients not found or inactive in Payme Business
    DEBIT_OPERATION_FAILED = 2  # Debit operation failed in processing center
    TRANSACTION_FAILED = 3  # Transaction execution error
    TIMEOUT = 4  # Transaction canceled due to timeout
    REFUNDED = 5  # Refunded
    UNKNOWN_ERROR = 10  # Unknown error

    @classmethod
    def choices(cls):
        return [(item.value, item.name) for item in cls]


class PaymeTransaction(TimestampMixin, Base):
    """
    Model for storing Payme payment gateway transactions.

    Attributes:
        id: Unique identifier for the transaction
        transaction_id: Unique transaction ID from Payme gateway
        perform_time: When the transaction was performed/completed
        cancel_time: When the transaction was canceled (if applicable)
        reason: Reason code for transaction cancellation
        amount: Transaction amount in smallest currency unit (tiyin)
        user_id: ID of the user who made the transaction
        promo_code_id: ID of the promo code being purchased
        status: Current transaction status (created/confirmed/canceled)
        created_at: Timestamp when transaction was created (from TimestampMixin)
        updated_at: Timestamp when transaction was last updated (from TimestampMixin)

    Relationships:
        user: The user who made this transaction
        promo_code: The promo code being purchased
    """
    __tablename__ = "payme_transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String(50), unique=True, nullable=False, index=True)
    perform_time = Column(DateTime(timezone=True), nullable=True)
    cancel_time = Column(DateTime(timezone=True), nullable=True)
    reason = Column(Integer, nullable=True)
    amount = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    promo_code_id = Column(Integer, ForeignKey("promo_codes.id"), nullable=False, index=True)
    status = Column(
        Integer,
        nullable=False,
        default=TransactionStatus.CREATED
    )

    # Relationships
    user = relationship("User", backref="payme_transactions")
    promo_code = relationship("PromoCode", backref="payme_transaction", uselist=False)

    class Meta:
        ordering = ["-created_at"]

    def __repr__(self):
        return f"<PaymeTransaction {self.transaction_id}: {self.status}>"

    @property
    def status_display(self):
        """Get human-readable status"""
        return TransactionStatus(self.status).name

    @property
    def reason_display(self):
        """Get human-readable cancellation reason"""
        if self.reason:
            return TransactionReason(self.reason).name
        return None

    def to_dict(self):
        """Convert transaction to dictionary for API responses"""
        return {
            "id": self.transaction_id,
            "user_id": self.user_id,
            "promo_code_id": self.promo_code_id,
            "amount": self.amount,
            "state": self.status,
            "created_at": self.created_at,
            "perform_time": self.perform_time,
            "cancel_time": self.cancel_time,
            "reason": self.reason,
        }

    def to_payme_format(self):
        """Convert to Payme API format"""
        from datetime import timezone as tz

        def to_millis(dt: Optional[datetime]) -> int:
            if dt is None:
                return 0
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=tz.utc)
            return int(dt.timestamp() * 1000)

        return {
            "id": self.transaction_id,
            "amount": self.amount,
            "account": {"promo_code_id": self.promo_code_id},
            "create_time": to_millis(self.created_at),
            "perform_time": to_millis(self.perform_time),
            "cancel_time": to_millis(self.cancel_time),
            "transaction": self.id,
            "state": self.status,
            "reason": self.reason,
        }
