"""Payme payment gateway service.

This service handles all Payme-related business logic including:
- Transaction management
- Payment verification
- Error handling
- Database operations

Reference: https://developer.help.paycom.uz/
"""
import base64
import structlog
from typing import Optional, Tuple, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from models import PaymeTransaction, PromoCode, User
from models.payme_transaction import TransactionStatus, TransactionReason
from config import settings

logger = structlog.get_logger()


class PaymeService:
    """Service for handling Payme payment operations."""

    # Payme error codes (from official documentation)
    ERROR_INTERNAL_SYSTEM = -32400
    ERROR_INSUFFICIENT_PRIVILEGE = -32504
    ERROR_INVALID_JSON_RPC_OBJECT = -32600
    ERROR_METHOD_NOT_FOUND = -32601
    ERROR_INVALID_AMOUNT = -31001
    ERROR_TRANSACTION_NOT_FOUND = -31003
    ERROR_INVALID_ACCOUNT = -31050
    ERROR_COULD_NOT_PERFORM = -31008
    ERROR_COULD_NOT_CANCEL = -31007

    @staticmethod
    def validate_auth(auth_header: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Validate Payme merchant authorization.

        Payme uses HTTP Basic Auth with login:key encoded in base64.

        Args:
            auth_header: Authorization header from request

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not auth_header:
            return False, "Missing authorization header"

        if not auth_header.startswith("Basic "):
            return False, "Invalid authorization format"

        try:
            # Decode base64 credentials
            encoded_credentials = auth_header.replace("Basic ", "")
            decoded_credentials = base64.b64decode(encoded_credentials).decode("utf-8")
            login, key = decoded_credentials.split(":", 1)

            # Validate credentials
            if login != settings.payme_login or key != settings.payme_key:
                return False, "Invalid credentials"

            return True, None

        except Exception as e:
            logger.error("Authorization validation error", error=str(e))
            return False, "Authorization validation failed"

    @staticmethod
    def validate_amount(amount: int) -> bool:
        """
        Validate transaction amount.

        Args:
            amount: Amount in tiyin (1 UZS = 100 tiyin)

        Returns:
            True if amount is valid
        """
        return amount == settings.app_price

    @staticmethod
    def validate_account(promo_code_id: int, db: Session) -> Tuple[bool, Optional[str], Optional[PromoCode]]:
        """
        Validate that the promo code exists and is available for purchase.

        Args:
            promo_code_id: Promo code ID
            db: Database session

        Returns:
            Tuple of (is_valid, error_message, promo_code)
        """
        promo_code = db.query(PromoCode).filter(PromoCode.id == promo_code_id).first()

        if not promo_code:
            return False, "Promo code not found", None

        if promo_code.is_used:
            return False, "Promo code already used", None

        return True, None, promo_code

    @staticmethod
    def check_perform_transaction(
            amount: int,
            promo_code_id: int,
            db: Session
    ) -> Tuple[bool, Optional[dict]]:
        """
        Check if transaction can be performed (CheckPerformTransaction method).

        Validates:
        - Amount matches APP_PRICE
        - Promo code exists and is available

        Args:
            amount: Transaction amount in tiyin
            promo_code_id: Promo code ID
            db: Database session

        Returns:
            Tuple of (success, error_dict)
        """
        # Validate amount
        if not PaymeService.validate_amount(amount):
            return False, {
                "code": PaymeService.ERROR_INVALID_AMOUNT,
                "message": "Invalid amount",
                "data": f"Expected {settings.app_price} tiyin"
            }

        # Validate account (promo code)
        is_valid, error_msg, _ = PaymeService.validate_account(promo_code_id, db)
        if not is_valid:
            return False, {
                "code": PaymeService.ERROR_INVALID_ACCOUNT,
                "message": "Invalid account",
                "data": error_msg
            }

        return True, None

    @staticmethod
    def create_transaction(
            transaction_id: str,
            time: int,
            amount: int,
            promo_code_id: int,
            user_id: int,
            db: Session
    ) -> Tuple[Optional[PaymeTransaction], Optional[dict]]:
        """
        Create a new transaction (CreateTransaction method).

        Args:
            transaction_id: Unique transaction ID from Payme
            time: Transaction creation time in milliseconds
            amount: Amount in tiyin
            promo_code_id: Promo code ID
            user_id: User ID (extracted from order context)
            db: Database session

        Returns:
            Tuple of (transaction, error_dict)
        """
        try:
            # Check if transaction already exists
            existing_transaction = db.query(PaymeTransaction).filter(
                PaymeTransaction.transaction_id == transaction_id
            ).first()

            if existing_transaction:
                # Transaction already exists, return it
                return existing_transaction, None

            # Validate amount
            if not PaymeService.validate_amount(amount):
                return None, {
                    "code": PaymeService.ERROR_INVALID_AMOUNT,
                    "message": "Invalid amount",
                    "data": f"Expected {settings.app_price} tiyin"
                }

            # Validate account
            is_valid, error_msg, promo_code = PaymeService.validate_account(promo_code_id, db)
            if not is_valid:
                return None, {
                    "code": PaymeService.ERROR_INVALID_ACCOUNT,
                    "message": "Invalid account",
                    "data": error_msg
                }

            # Create transaction
            transaction = PaymeTransaction(
                transaction_id=transaction_id,
                amount=amount,
                user_id=user_id,
                promo_code_id=promo_code_id,
                status=TransactionStatus.CREATED,
                created_at=datetime.fromtimestamp(time / 1000, tz=timezone.utc)
            )

            db.add(transaction)
            db.commit()
            db.refresh(transaction)

            logger.info(
                "Transaction created",
                transaction_id=transaction_id,
                user_id=user_id,
                promo_code_id=promo_code_id,
                amount=amount
            )

            return transaction, None

        except Exception as e:
            logger.error("Error creating transaction", error=str(e))
            db.rollback()
            return None, {
                "code": PaymeService.ERROR_INTERNAL_SYSTEM,
                "message": "Internal server error",
                "data": str(e)
            }

    @staticmethod
    def perform_transaction(
            transaction_id: str,
            db: Session
    ) -> tuple[None, dict[str, int | str]] | tuple[type[PaymeTransaction], None]:
        """
        Perform (confirm) a transaction (PerformTransaction method).

        This marks the transaction as successful and activates the promo code.

        Args:
            transaction_id: Payme transaction ID
            db: Database session

        Returns:
            Tuple of (transaction, error_dict)
        """
        try:
            # Find transaction
            transaction = db.query(PaymeTransaction).filter(
                PaymeTransaction.transaction_id == transaction_id
            ).first()

            if not transaction:
                return None, {
                    "code": PaymeService.ERROR_TRANSACTION_NOT_FOUND,
                    "message": "Transaction not found"
                }

            # If already performed, return it
            if transaction.status == TransactionStatus.CONFIRMED:
                return transaction, None

            # Check if transaction can be performed
            if transaction.status not in [TransactionStatus.CREATED]:
                return None, {
                    "code": PaymeService.ERROR_COULD_NOT_PERFORM,
                    "message": "Could not perform transaction",
                    "data": f"Invalid transaction state: {transaction.status}"
                }

            # Update transaction status
            transaction.status = TransactionStatus.CONFIRMED
            transaction.perform_time = datetime.now(timezone.utc)

            # Activate the promo code
            promo_code = db.query(PromoCode).filter(
                PromoCode.id == transaction.promo_code_id
            ).first()

            if promo_code:
                promo_code.is_used = True
                promo_code.used_at = datetime.now(timezone.utc)
                promo_code.user_id = transaction.user_id

            db.commit()
            db.refresh(transaction)

            logger.info(
                "Transaction performed",
                transaction_id=transaction_id,
                user_id=transaction.user_id,
                promo_code_id=transaction.promo_code_id
            )

            return transaction, None

        except Exception as e:
            logger.error("Error performing transaction", error=str(e))
            db.rollback()
            return None, {
                "code": PaymeService.ERROR_INTERNAL_SYSTEM,
                "message": "Internal server error",
                "data": str(e)
            }

    @staticmethod
    def cancel_transaction(
            transaction_id: str,
            reason: int,
            db: Session
    ) -> Tuple[Optional[PaymeTransaction], Optional[dict]]:
        """
        Cancel a transaction (CancelTransaction method).

        Args:
            transaction_id: Payme transaction ID
            reason: Cancellation reason code
            db: Database session

        Returns:
            Tuple of (transaction, error_dict)
        """
        try:
            # Find transaction
            transaction = db.query(PaymeTransaction).filter(
                PaymeTransaction.transaction_id == transaction_id
            ).first()

            if not transaction:
                return None, {
                    "code": PaymeService.ERROR_TRANSACTION_NOT_FOUND,
                    "message": "Transaction not found"
                }

            # If already canceled, return it
            if transaction.status in [
                TransactionStatus.CANCELED_BEFORE_CONFIRM,
                TransactionStatus.CANCELED_AFTER_CONFIRM
            ]:
                return transaction, None

            # Determine cancel status based on current status
            if transaction.status == TransactionStatus.CREATED:
                transaction.status = TransactionStatus.CANCELED_BEFORE_CONFIRM
            elif transaction.status == TransactionStatus.CONFIRMED:
                transaction.status = TransactionStatus.CANCELED_AFTER_CONFIRM

                # Revert promo code activation if transaction was confirmed
                promo_code = db.query(PromoCode).filter(
                    PromoCode.id == transaction.promo_code_id
                ).first()

                if promo_code:
                    promo_code.is_used = False
                    promo_code.used_at = None
                    promo_code.user_id = None
            else:
                return None, {
                    "code": PaymeService.ERROR_COULD_NOT_CANCEL,
                    "message": "Could not cancel transaction",
                    "data": f"Invalid transaction state: {transaction.status}"
                }

            transaction.cancel_time = datetime.now(timezone.utc)
            transaction.reason = reason

            db.commit()
            db.refresh(transaction)

            logger.info(
                "Transaction canceled",
                transaction_id=transaction_id,
                reason=reason,
                status=transaction.status
            )

            return transaction, None

        except Exception as e:
            logger.error("Error canceling transaction", error=str(e))
            db.rollback()
            return None, {
                "code": PaymeService.ERROR_INTERNAL_SYSTEM,
                "message": "Internal server error",
                "data": str(e)
            }

    @staticmethod
    def check_transaction(
            transaction_id: str,
            db: Session
    ) -> Tuple[Optional[PaymeTransaction], Optional[dict]]:
        """
        Check transaction status (CheckTransaction method).

        Args:
            transaction_id: Payme transaction ID
            db: Database session

        Returns:
            Tuple of (transaction, error_dict)
        """
        transaction = db.query(PaymeTransaction).filter(
            PaymeTransaction.transaction_id == transaction_id
        ).first()

        if not transaction:
            return None, {
                "code": PaymeService.ERROR_TRANSACTION_NOT_FOUND,
                "message": "Transaction not found"
            }

        return transaction, None

    @staticmethod
    def get_statement(
            from_time: int,
            to_time: int,
            db: Session
    ) -> list[PaymeTransaction]:
        """
        Get transactions for a time period (GetStatement method).

        Args:
            from_time: Start timestamp in milliseconds
            to_time: End timestamp in milliseconds
            db: Database session

        Returns:
            List of transactions
        """
        from_datetime = datetime.fromtimestamp(from_time / 1000, tz=timezone.utc)
        to_datetime = datetime.fromtimestamp(to_time / 1000, tz=timezone.utc)

        transactions = db.query(PaymeTransaction).filter(
            PaymeTransaction.created_at >= from_datetime,
            PaymeTransaction.created_at <= to_datetime
        ).all()

        return transactions

    @staticmethod
    def generate_payment_url(
            user_id: int,
            promo_code_id: int,
            amount: int
    ) -> str:
        """
        Generate Payme checkout URL for frontend.

        Args:
            user_id: User ID
            promo_code_id: Promo code ID
            amount: Amount in tiyin

        Returns:
            Payme checkout URL
        """
        merchant_id = settings.payme_merchant_id

        # Encode account in base64
        account = f"promo_code_id={promo_code_id}"
        encoded_account = base64.b64encode(account.encode()).decode()

        # Generate URL
        url = f"{settings.payme_host}/api?m={merchant_id}&ac.{encoded_account}&a={amount}"

        logger.info(
            "Payment URL generated",
            user_id=user_id,
            promo_code_id=promo_code_id,
            amount=amount
        )

        return url
