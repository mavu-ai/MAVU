"""API dependencies for FastAPI endpoints."""
from dependencies.database import get_db
from dependencies.auth import (
    get_current_user,
    get_current_admin_user,
    get_user_id_from_header,
    require_admin,
    verify_admin_key
)

# Re-export for convenience
__all__ = [
    "get_db",
    "get_current_user",
    "get_current_admin_user",
    "get_user_id_from_header",
    "require_admin",
    "verify_admin_key"
]
