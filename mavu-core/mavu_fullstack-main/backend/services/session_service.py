"""Session management service for user authentication."""
import secrets
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from models import Session as SessionModel, User
import structlog

logger = structlog.get_logger()


class SessionService:
    """Service for managing user authentication sessions."""

    @staticmethod
    def generate_session_token() -> str:
        """Generate a secure session token."""
        return secrets.token_urlsafe(32)

    @staticmethod
    def create_session(
            db: Session,
            user_id: int,
            ip_address: Optional[str] = None,
            user_agent: Optional[str] = None,
            expires_in_days: Optional[int] = None
    ) -> str:
        """
        Create a new session for a user.

        Args:
            db: Database session
            user_id: ID of the user
            ip_address: IP address of the client
            user_agent: User agent string
            expires_in_days: Days until session expires (None = non-expiring for guest users)

        Returns:
            Session token string
        """
        # Generate unique session token
        session_token = SessionService.generate_session_token()

        # Calculate expiration time (None for guest users)
        expires_at = None
        if expires_in_days:
            expires_at = datetime.now() + timedelta(days=expires_in_days)

        # Create session record
        session = SessionModel(
            user_id=user_id,
            session_token=session_token,
            is_active=True,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent
        )

        db.add(session)
        db.commit()
        db.refresh(session)

        logger.info(
            "Session created",
            user_id=user_id,
            session_id=session.id,
            expires_at=expires_at
        )

        return session_token

    @staticmethod
    def validate_session(db: Session, session_token: str) -> Optional[User]:
        """
        Validate a session token and return the associated user.

        Args:
            db: Database session
            session_token: Session token to validate

        Returns:
            User object if session is valid, None otherwise
        """
        # Find active session
        session = db.query(SessionModel).filter(
            SessionModel.session_token == session_token,
            SessionModel.is_active == True
        ).first()

        if not session:
            logger.warning("Session not found", session_token=session_token[:8])
            return None

        # Check if session has expired
        if session.expires_at and session.expires_at < datetime.now():
            logger.warning("Session expired", session_id=session.id, user_id=session.user_id)
            session.is_active = False
            db.commit()
            return None

        # Get user
        user = db.query(User).filter(User.id == session.user_id).first()

        if not user or not user.is_active:
            logger.warning("User not found or inactive", user_id=session.user_id)
            return None

        return user

    @staticmethod
    def invalidate_session(db: Session, session_token: str) -> bool:
        """
        Invalidate a session.

        Args:
            db: Database session
            session_token: Session token to invalidate

        Returns:
            True if session was invalidated, False otherwise
        """
        session = db.query(SessionModel).filter(
            SessionModel.session_token == session_token
        ).first()

        if not session:
            return False

        session.is_active = False
        db.commit()

        logger.info("Session invalidated", session_id=session.id, user_id=session.user_id)
        return True

    @staticmethod
    def invalidate_user_sessions(db: Session, user_id: int) -> int:
        """
        Invalidate all sessions for a user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Number of sessions invalidated
        """
        count = db.query(SessionModel).filter(
            SessionModel.user_id == user_id,
            SessionModel.is_active == True
        ).update({"is_active": False})

        db.commit()

        logger.info("User sessions invalidated", user_id=user_id, count=count)
        return count
