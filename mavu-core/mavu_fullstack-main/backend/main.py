"""Main FastAPI application."""
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import structlog
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from config import settings
from api.v1.api import api_router
from utils.weaviate_client import weaviate_client
from utils.redis_client import redis_client
from api.v1.endpoints.health.schemas import HealthCheckResponse
from admin import create_admin
from dependencies.database import init_db

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.dev.ConsoleRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Telegram Bot imports (optional - only if token is configured)
TELEGRAM_BOT_ENABLED = False
try:
    if settings.telegram_bot_token:
        from api.v1.endpoints.telegram import bot, dp

        TELEGRAM_BOT_ENABLED = True
        logger.info("Telegram bot initialized")
    else:
        logger.info("Telegram bot disabled (no token configured)")
except Exception as e:
    logger.warning("Failed to initialize Telegram bot", error=str(e))

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Application lifespan manager."""
    # Startup
    import os
    import multiprocessing

    # Get worker/process info to prevent duplicate initialization
    is_main_worker = os.getenv("UVICORN_WORKER_ID", "0") == "0" or multiprocessing.current_process().name == "MainProcess"

    logger.info("Starting MavuAI application", version=settings.app_version, worker_id=os.getenv("UVICORN_WORKER_ID", "main"))

    # Initialize database tables (only in main worker to avoid duplicate attempts)
    if is_main_worker:
        try:
            await asyncio.to_thread(init_db)
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize database", error=str(e))
            # Continue running - tables might already exist

    # Connect to Weaviate (each worker needs its own connection)
    try:
        await weaviate_client.connect()
        logger.info("Connected to Weaviate")
    except Exception as e:
        logger.error("Failed to connect to Weaviate", error=str(e))
        # Continue running even if Weaviate is unavailable initially

    # Connect to Redis (each worker needs its own connection)
    try:
        await redis_client.connect()
        logger.info("Connected to Redis")
    except Exception as e:
        logger.warning("Failed to connect to Redis - operating without cache", error=str(e))
        # Continue running even if Redis is unavailable (graceful degradation)

    # Start Telegram bot (only in main worker)
    if TELEGRAM_BOT_ENABLED and is_main_worker:
        try:
            await dp.emit_startup()
            logger.info("Telegram bot started")
            logger.info("Use CLI to setup webhook: python -m cli setup-webhook")
        except Exception as e:
            logger.error("Failed to start Telegram bot", error=str(e))

    yield

    # Shutdown
    logger.info("Shutting down MavuAI application", worker_id=os.getenv("UVICORN_WORKER_ID", "main"))

    # Shutdown Telegram bot (only in main worker)
    if TELEGRAM_BOT_ENABLED and is_main_worker:
        try:
            await dp.emit_shutdown()
            logger.info("Telegram bot shutdown complete")
        except Exception as e:
            logger.error("Failed to shutdown Telegram bot", error=str(e))

    # Disconnect from Weaviate
    await weaviate_client.disconnect()

    # Disconnect from Redis
    await redis_client.disconnect()


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Real-time Speech-to-Speech AI with RAG capabilities",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add session middleware for SQLAdmin authentication (must be added before admin)
app.add_middleware(
    SessionMiddleware,  # noqa
    secret_key=settings.secret_key,
    session_cookie="mavuai_admin_session",
    max_age=3600  # 1 hour
)

# Create SQLAdmin interface (must be done before other middleware)
admin = create_admin(app)


# Custom middleware class for WebSocket CORS handling
class WebSocketCORSMiddleware(BaseHTTPMiddleware):
    """
    Handle CORS for WebSocket connections.

    Mobile apps and web apps need proper CORS handling for WebSocket upgrades.
    This middleware bypasses standard CORS checks for WebSocket connections
    and relies on authentication for security instead.

    This middleware MUST run before CORSMiddleware to intercept WebSocket
    upgrade requests before CORS rejects them.
    """

    async def dispatch(self, request: Request, call_next):
        # Check if this is a WebSocket upgrade request
        is_websocket = request.headers.get("upgrade", "").lower() == "websocket"

        if is_websocket:
            origin = request.headers.get("origin")

            # Log WebSocket connection attempt
            if not origin:
                logger.info("WebSocket connection without Origin header (likely mobile app)")
            elif origin in settings.cors_origins:
                logger.info("WebSocket connection from allowed origin", origin=origin)
            elif settings.environment == "development" and origin.startswith("http://localhost"):
                logger.info("WebSocket connection from localhost (development)", origin=origin)
            else:
                logger.warning(
                    "WebSocket connection from non-whitelisted origin",
                    origin=origin,
                    allowed_origins=settings.cors_origins
                )

            # For WebSocket connections, we bypass CORS entirely
            # Authentication layer provides the real security
            response = await call_next(request)
            return response

        # Not a WebSocket request - let CORS middleware handle it
        return await call_next(request)


# Add CORS middleware FIRST (so it runs LAST, after WebSocket middleware)
cors_origins = settings.cors_origins
logger.info("Configured CORS origins", origins=cors_origins)

app.add_middleware(
    CORSMiddleware,  # noqa
    allow_origins=cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Add WebSocket CORS middleware SECOND (so it runs FIRST, before CORS)
# This logs WebSocket connection attempts and validates origins
app.add_middleware(WebSocketCORSMiddleware)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Include API v1 router
app.include_router(
    api_router,
    prefix="/api/v1"
)


@app.get("/", response_model=HealthCheckResponse)
async def root():
    """
    Root endpoint with API information.

    Returns basic health status and API metadata.
    """
    return HealthCheckResponse(
        status="healthy",
        version=settings.app_version,
        environment=settings.environment,
        timestamp=datetime.now()
    )


@app.get("/docs/mobile")
async def mobile_docs():
    """
    📱 Mobile WebSocket Integration Documentation

    Returns comprehensive integration guide for iOS and Android developers.
    Includes code examples, authentication methods, and troubleshooting.

    **Direct Link:** `/docs/MOBILE_WEBSOCKET_INTEGRATION.md`
    """
    from fastapi.responses import FileResponse
    from pathlib import Path

    docs_path = Path(__file__).parent / "docs" / "MOBILE_WEBSOCKET_INTEGRATION.md"

    if docs_path.exists():
        return FileResponse(
            path=docs_path,
            media_type="text/markdown",
            headers={
                "Content-Disposition": "inline; filename=MOBILE_WEBSOCKET_INTEGRATION.md"
            }
        )
    else:
        return JSONResponse(
            status_code=404,
            content={
                "error": "Mobile documentation not found",
                "message": "Please check /docs for API documentation"
            }
        )


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    Health check endpoint.

    Returns detailed health status including Weaviate and Redis connection status.
    """
    # Check Weaviate connection
    weaviate_status = "connected" if weaviate_client.client else "disconnected"

    # Check Redis connection
    redis_status = "connected" if redis_client.connected else "disconnected"

    # Overall status
    overall_status = "healthy" if weaviate_status == "connected" else "degraded"

    logger.info(
        "Health check",
        weaviate=weaviate_status,
        redis=redis_status,
        overall=overall_status
    )

    return HealthCheckResponse(
        status=overall_status,
        version=settings.app_version,
        environment=settings.environment,
        timestamp=datetime.now()
    )


# Error handlers
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error("Unhandled exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.debug else None
        }
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level="info" if settings.debug else "warning"
    )
