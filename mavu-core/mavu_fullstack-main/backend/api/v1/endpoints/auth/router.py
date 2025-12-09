"""Authentication router for user registration and login."""
import logging
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
from typing import Optional

from dependencies.database import get_db
from models import User
from services.session_service import SessionService
from services.promo_code_service import PromoCodeService
from services.user_cache import get_user_cache
from .schemas import RegisterRequest, RegisterResponse, ValidateResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/register", response_model=RegisterResponse)
async def register(
    request: RegisterRequest,
    req: Request,
    db: Session = Depends(get_db),
):
    """
    Register a new guest user with a promo code.
    Returns a non-expiring session token for immediate access.

    Requirements:
    - Active promo code that hasn't been used

    Guest users can:
    - Start using the app immediately after promo code validation
    - Save their progress
    - Later add email/name/profile information
    """
    try:
        # Validate promo code first
        is_valid, message, promo_code = PromoCodeService.validate_promo_code(
            db=db,
            code=request.promo_code,
        )

        if not is_valid:
            raise HTTPException(status_code=400, detail=message)

        # Create guest user with minimal information
        # Guest users are identified by having null name, age, and gender
        new_user = User(
            email=None,  # Guest users don't have email initially
            username=None,  # No username required
            telegram_id=None,  # Not a Telegram user
            name=None,  # Name will be collected through conversation
            age=None,  # Age will be collected through conversation
            gender=None,  # Gender will be inferred or collected
            language="ru",  # Default to Russian for guest users
            is_verified=False,
            is_active=True,
        )
        db.add(new_user)
        db.flush()  # Flush to get the user ID without committing

        # Store values we'll need after commit
        user_id = new_user.id

        # Activate promo code for this user
        # This will commit the transaction internally
        PromoCodeService.activate_promo_code(
            db=db,
            code=request.promo_code,
            user_id=user_id,
        )

        # Create non-expiring session for guest user
        # This will also commit internally
        session_token = SessionService.create_session(
            db=db,
            user_id=user_id,
            ip_address=req.client.host if req and req.client else None,
            user_agent=req.headers.get("user-agent") if req else None,
            expires_in_days=None  # Non-expiring for guest users
        )

        # Re-query the user to get a fresh instance attached to the session
        new_user = db.query(User).filter(User.id == user_id).first()

        # Invalidate cache for this user (in case they're logging in from another device)
        cache = get_user_cache()
        cache.invalidate(user_id)

        logger.info(f"Guest user {user_id} registered with promo code {request.promo_code}")

        return RegisterResponse(
            user_id=user_id,
            session_token=session_token,
            status="guest",
            created_at=new_user.created_at,
            message="Guest user created successfully with promo code!"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Guest registration error: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Registration failed")


@router.get("/validate", response_model=ValidateResponse)
async def validate_session(
    x_session_token: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """
    Validate the current session token and return user information.

    This endpoint checks if the session token is still valid and returns
    the associated user's profile information.

    Headers:
    - X-Session-Token: The session token to validate

    Returns:
    - valid: True if session is valid, False otherwise
    - user_id: User's ID if valid
    - email, name, age, gender: User profile information
    - is_guest: True if user has not completed profile
    - is_registered: True if user has completed profile (name, age, gender)
    """
    if not x_session_token:
        return ValidateResponse(
            valid=False,
            message="No session token provided"
        )

    # Validate session and get user
    user = SessionService.validate_session(db, x_session_token)

    if not user:
        return ValidateResponse(
            valid=False,
            message="Invalid or expired session"
        )

    # Return user information
    return ValidateResponse(
        valid=True,
        user_id=user.id,
        email=user.email,
        name=user.name,
        age=user.age,
        gender=user.gender,
        is_guest=user.is_guest,
        is_registered=user.is_registered,
        message="Session is valid"
    )
