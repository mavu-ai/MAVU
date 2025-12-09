"""Authentication and authorization dependencies."""
from typing import Optional
from fastapi import Depends, HTTPException, Header, status, Query
from sqlalchemy.orm import Session
import structlog
from starlette.websockets import WebSocket, WebSocketDisconnect

from config import settings
from dependencies.database import get_db
from models.user import User
from services.session_service import SessionService
from services.user_cache import get_user_cache
from utils.telegram import validate_telegram_webapp_request

logger = structlog.get_logger()


def get_or_create_user_from_telegram_id(
    telegram_id: int,
    user_info: dict,
    db: Session
) -> type[User] | User:
    """
    Get or create a user by telegram_id.

    Auto-registers new Telegram users with their profile information.

    Args:
        telegram_id: Telegram user ID
        user_info: User information from Telegram initData
        db: Database session

    Returns:
        User object (existing or newly created)
    """
    # Check if user already exists
    user = db.query(User).filter(User.telegram_id == telegram_id).first()

    if user:
        logger.info("Existing Telegram user found", telegram_id=telegram_id, user_id=user.id)
        return user

    # Create new user from Telegram data (as guest user initially)
    # Name will be extracted conversationally during chat
    new_user = User(
        telegram_id=telegram_id,
        username=user_info.get('username'),
        name=None,  # Will be extracted during conversation
        age=None,  # Will be extracted during conversation
        gender=None,  # Will be extracted during conversation
        language=user_info.get('language_code', 'en'),
        is_active=True,
        is_verified=True,  # Telegram users are pre-verified
        email=None,
        password_hash=None
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    logger.info(
        "New Telegram user created",
        telegram_id=telegram_id,
        user_id=new_user.id,
        username=user_info.get('username')
    )

    return new_user


async def get_user_from_telegram_init_data(
    x_telegram_init_data: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Authenticate user from Telegram Web App initData.

    This validates the Telegram initData signature and returns the authenticated user.
    Auto-creates users if they don't exist (Telegram users are pre-verified).

    Args:
        x_telegram_init_data: Telegram Web App initData from header
        db: Database session

    Returns:
        User object if initData is valid, None otherwise
    """
    if not x_telegram_init_data:
        return None

    # Validate Telegram initData
    is_valid, user_info = validate_telegram_webapp_request(x_telegram_init_data)

    if not is_valid or not user_info:
        logger.warning("Invalid Telegram initData in authentication")
        return None

    telegram_id = user_info.get('telegram_id')
    if not telegram_id:
        logger.warning("No telegram_id in validated initData")
        return None

    # Get or create user
    user = get_or_create_user_from_telegram_id(telegram_id, user_info, db)

    # Cache the user
    cache = get_user_cache()
    cache.set(user)

    return user


async def get_user_from_session_token(
    x_session_token: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get current user from session token.

    Supports both X-Session-Token header and Authorization: Bearer header.
    Uses caching for performance optimization.

    Args:
        x_session_token: Session token from X-Session-Token header
        authorization: Bearer token from Authorization header
        db: Database session

    Returns:
        User object if session is valid, None otherwise
    """
    # Get session token from either header
    session_token = x_session_token
    if not session_token and authorization:
        if authorization.startswith("Bearer "):
            session_token = authorization[7:]

    if not session_token:
        return None

    # Check cache first for performance
    cache = get_user_cache()
    cached_user = cache.get_by_session(session_token)
    if cached_user:
        return cached_user

    # Validate session with database
    user = SessionService.validate_session(db, session_token)
    if user:
        # Cache the user for future requests
        cache.set(user, session_token)

    return user


async def get_user_id_from_header(
    x_user_id: Optional[str] = Header(None),
    x_telegram_init_data: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None),
    x_session_token: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> str:
    """
    Get current user ID from headers.

    Supports multiple authentication methods:
    1. X-Telegram-Init-Data header (for Telegram Web App users)
    2. X-Session-Token header (preferred for authenticated users)
    3. Authorization: Bearer header (alternative session token)
    4. X-User-Id header (legacy support for development)

    Returns user ID (integer as string) for API usage.
    """
    # Try Telegram authentication first
    if x_telegram_init_data:
        user = await get_user_from_telegram_init_data(x_telegram_init_data, db)
        if user:
            return str(user.id)

    # Try session token (preferred method)
    user = await get_user_from_session_token(x_session_token, authorization, db)
    if user:
        return str(user.id)

    # Fall back to X-User-Id for development/legacy support
    if x_user_id:
        # Try to interpret as telegram_id or database ID
        try:
            user_id_int = int(x_user_id)
            # Check if it's a database ID
            user = db.query(User).filter(User.id == user_id_int).first()
            if user:
                return str(user.id)
        except ValueError:
            pass
        # Legacy string format support (return as-is for development)
        return x_user_id

    # Default user for development
    if settings.environment == "development":
        return "default_user"

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Please provide X-Telegram-Init-Data, X-Session-Token or X-User-Id header."
    )


async def get_user_id_from_websocket(
    websocket: WebSocket,
    user_id: Optional[str] = Query(None),
    session_token: Optional[str] = Query(None),
    db: Session = Depends(get_db)
) -> str:
    """
    Extract and validate user ID from WebSocket connection.

    Supports multiple authentication methods:
    1. session_token query parameter (preferred for authenticated users)
    2. user_id query parameter (legacy support for development)
    3. X-Session-Token header
    4. Authorization header

    Args:
        websocket: WebSocket connection
        user_id: User ID from query parameter
        session_token: Session token from query parameter
        db: Database session

    Returns:
        User ID string
    """
    # Try session token from query parameter first
    if session_token:
        cache = get_user_cache()
        cached_user = cache.get_by_session(session_token)

        if cached_user:
            logger.info("WebSocket auth via cached session", user_id=cached_user.id)
            return str(cached_user.id)

        # Validate session from database
        user = SessionService.validate_session(db, session_token)
        if user:
            cache.set(user, session_token)
            logger.info("WebSocket auth via session token", user_id=user.id)
            return str(user.id)

    # Try session token from headers
    headers = dict(websocket.headers)
    header_session_token = headers.get(b"x-session-token") or headers.get(b"authorization")

    if header_session_token:
        token_str = header_session_token.decode() if isinstance(header_session_token, bytes) else header_session_token

        # Handle Bearer token format
        if token_str.startswith("Bearer "):
            token_str = token_str[7:]

        cache = get_user_cache()
        cached_user = cache.get_by_session(token_str)

        if cached_user:
            logger.info("WebSocket auth via cached header session", user_id=cached_user.id)
            return str(cached_user.id)

        user = SessionService.validate_session(db, token_str)
        if user:
            cache.set(user, token_str)
            logger.info("WebSocket auth via header session token", user_id=user.id)
            return str(user.id)

    # Fall back to user_id query parameter for development
    if user_id:
        logger.info("WebSocket auth via user_id parameter", user_id=user_id)
        return user_id

    # Default user for development
    if settings.environment == "development":
        logger.warning("WebSocket using default_user (development mode)")
        return "default_user"

    # In production, reject unauthenticated connections
    logger.error(
        "WebSocket connection rejected: no authentication provided",
        environment=settings.environment,
        has_session_token=bool(session_token),
        has_user_id=bool(user_id),
        headers=list(headers.keys())
    )

    # Close with proper WebSocket close code
    await websocket.close(code=1008, reason="Authentication required")
    raise WebSocketDisconnect(code=1008, reason="Authentication required")


async def get_current_user(
    x_user_id: Optional[str] = Header(None),
    x_session_token: Optional[str] = Header(None),
    x_telegram_init_data: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user.

    Supports multiple authentication methods (in priority order):
    1. X-Telegram-Init-Data header (for Telegram Web App users)
    2. X-Session-Token header (for authenticated web/mobile users)
    3. Authorization: Bearer header (alternative session token)
    4. X-User-Id header (legacy support for development)

    Raises HTTPException if user is not authenticated or not active.
    """
    # Try Telegram authentication first (highest priority)
    if x_telegram_init_data:
        user = await get_user_from_telegram_init_data(x_telegram_init_data, db)
        if user:
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User account is inactive"
                )
            return user

    # Try session token authentication
    user = await get_user_from_session_token(x_session_token, authorization, db)
    if user:
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )
        return user

    # Fall back to X-User-Id for development/legacy support
    if x_user_id:
        # Try to interpret as database ID
        try:
            user_id_int = int(x_user_id)
            user = db.query(User).filter(User.id == user_id_int).first()
        except ValueError:
            # Not a valid integer - try telegram_id or email
            try:
                telegram_id = int(x_user_id)
                user = db.query(User).filter(User.telegram_id == telegram_id).first()
            except ValueError:
                # Try as email
                user = db.query(User).filter(User.email == x_user_id).first()

        # Auto-create guest user if doesn't exist (for development only)
        if not user and settings.environment == "development":
            user = User(is_active=True, language='en')
            db.add(user)
            db.commit()
            db.refresh(user)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )

        return user

    # No authentication provided
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Please provide X-Telegram-Init-Data, X-Session-Token, Authorization, or X-User-Id header."
    )


async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Verify that the current user has admin privileges.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


async def require_admin(
    x_admin_key: Optional[str] = Header(None)
) -> bool:
    """
    Require admin privileges (legacy support).

    In production, this should validate admin tokens.
    """
    # Simple admin key check for development
    if x_admin_key == settings.admin_secret_key:
        return True

    raise HTTPException(
        status_code=403,
        detail="Admin privileges required"
    )


async def verify_admin_key(
    x_admin_key: Optional[str] = Header(None)
) -> bool:
    """
    Verify admin API key from header.

    Usage for system-level operations that don't require user context.
    """
    if not x_admin_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-Admin-Key header is required"
        )

    if x_admin_key != settings.admin_secret_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin key"
        )

    return True