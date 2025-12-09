"""API v1 router aggregation."""
from fastapi import APIRouter

# Import from new structure
from .endpoints.profile import router as profile_router
from .endpoints.realtime import router as realtime_router
from .endpoints.health import router as health_router
from .endpoints.auth import router as auth_router
from .endpoints.telegram import router as telegram_router
from .endpoints.payme import router as payme_router

api_router = APIRouter()

# Include all routers with appropriate prefixes and tags

# Authentication endpoints
api_router.include_router(
    auth_router,
    prefix="/auth",
    tags=["auth"]
)

# User profile endpoints
api_router.include_router(
    profile_router,
    prefix="/profile",
    tags=["profile"]
)

# Real-time WebSocket endpoint
api_router.include_router(
    realtime_router,
    prefix="/realtime",
    tags=["realtime"]
)

# Health check and test endpoints
api_router.include_router(
    health_router,
    prefix="/health",
    tags=["health"]
)

# Telegram bot webhook and Web App endpoints
api_router.include_router(
    telegram_router,
    prefix="/telegram",
    tags=["telegram"]
)

# Payme payment gateway endpoints
api_router.include_router(
    payme_router,
    prefix="/payme",
    tags=["payme"]
)

__all__ = ["api_router"]
