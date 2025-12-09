"""User caching service for performance optimization."""
from typing import Optional
import structlog

from models import User

logger = structlog.get_logger()


class UserCache:
    """
    Simple in-memory user cache for performance optimization.

    Note: This is a simple implementation. In production, consider using Redis.
    """

    def __init__(self):
        """Initialize user cache."""
        self._cache: dict[int, User] = {}  # user_id -> User
        self._session_cache: dict[str, User] = {}  # session_token -> User

    def get(self, user_id: int) -> Optional[User]:
        """
        Get user from cache by user ID.

        Args:
            user_id: User ID

        Returns:
            User object if found in cache, None otherwise
        """
        user = self._cache.get(user_id)
        if user:
            logger.debug("User cache hit", user_id=user_id)
        return user

    def get_by_session(self, session_token: str) -> Optional[User]:
        """
        Get user from cache by session token.

        Args:
            session_token: Session token

        Returns:
            User object if found in cache, None otherwise
        """
        user = self._session_cache.get(session_token)
        if user:
            logger.debug("Session cache hit", session_token=session_token[:8])
        return user

    def set(self, user: User, session_token: Optional[str] = None) -> None:
        """
        Add user to cache.

        Args:
            user: User object to cache
            session_token: Optional session token to associate with user
        """
        self._cache[user.id] = user

        if session_token:
            self._session_cache[session_token] = user

        logger.debug("User cached", user_id=user.id, has_session=bool(session_token))

    def invalidate(self, user_id: int) -> None:
        """
        Remove user from cache.

        Args:
            user_id: User ID to invalidate
        """
        # Remove from user cache
        if user_id in self._cache:
            del self._cache[user_id]
            logger.debug("User cache invalidated", user_id=user_id)

        # Remove from session cache (need to find and remove all entries)
        sessions_to_remove = [
            token for token, user in self._session_cache.items()
            if user.id == user_id
        ]
        for token in sessions_to_remove:
            del self._session_cache[token]

    def clear(self) -> None:
        """Clear entire cache."""
        self._cache.clear()
        self._session_cache.clear()
        logger.info("User cache cleared")


# Global cache instance
_user_cache: Optional[UserCache] = None


def get_user_cache() -> UserCache:
    """
    Get global user cache instance.

    Returns:
        UserCache instance
    """
    global _user_cache
    if _user_cache is None:
        _user_cache = UserCache()
    return _user_cache
