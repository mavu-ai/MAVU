"""Promo code validation and activation service."""
from datetime import datetime

from sqlalchemy.orm import Session

from models import PromoCode
import structlog

logger = structlog.get_logger()


class PromoCodeService:
    """Service for validating and activating promotional codes."""

    @staticmethod
    def validate_promo_code(
            db: Session,
            code: str
    ) -> tuple[bool, str, None] | tuple[bool, str, type[PromoCode]]:
        """
        Validate a promotional code.

        Args:
            db: Database session
            code: Promo code string to validate

        Returns:
            Tuple of (is_valid, message, promo_code_object)
        """
        # Find promo code
        promo_code = db.query(PromoCode).filter(
            PromoCode.code == code.strip().upper()
        ).first()

        if not promo_code:
            logger.warning("Promo code not found", code=code)
            return False, "Invalid promo code", None

        # Check if already used
        if not promo_code.is_active:
            logger.warning("Promo code already used", code=code, user_id=promo_code.user_id)
            return False, "This promo code has already been used", None

        logger.info("Promo code validated", code=code)
        return True, "Valid promo code", promo_code

    @staticmethod
    def activate_promo_code(
            db: Session,
            code: str,
            user_id: int
    ) -> bool:
        """
        Activate a promo code for a user.

        Args:
            db: Database session
            code: Promo code string
            user_id: ID of the user activating the code

        Returns:
            True if activation successful, False otherwise
        """
        # Find promo code
        promo_code = db.query(PromoCode).filter(
            PromoCode.code == code.strip().upper(),
            PromoCode.is_active == True
        ).first()

        if not promo_code:
            logger.error("Cannot activate promo code - not found or already used", code=code)
            return False

        # Activate the promo code
        promo_code.is_active = False
        promo_code.user_id = user_id
        promo_code.activated_at = datetime.now()

        db.commit()

        logger.info("Promo code activated", code=code, user_id=user_id)
        return True

    @staticmethod
    def create_promo_code(db: Session, code: str) -> PromoCode:
        """
        Create a new promo code.

        Args:
            db: Database session
            code: Promo code string

        Returns:
            Created PromoCode object
        """
        promo_code = PromoCode(
            code=code.strip().upper(),
            is_active=True
        )

        db.add(promo_code)
        db.commit()
        db.refresh(promo_code)

        logger.info("Promo code created", code=code)
        return promo_code

    @staticmethod
    def get_unused_promo_codes(db: Session, limit: int = 100) -> list[type[PromoCode]]:
        """
        Get list of unused promo codes.

        Args:
            db: Database session
            limit: Maximum number of codes to return

        Returns:
            List of unused PromoCode objects
        """
        return db.query(PromoCode).filter(
            PromoCode.is_active == True
        ).limit(limit).all()
