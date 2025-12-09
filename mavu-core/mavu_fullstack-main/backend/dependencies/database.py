"""Database session dependency and utilities."""
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from config import settings
import structlog

logger = structlog.get_logger()


def get_sync_database_url(database_url: str) -> str:
    """Convert async database URL to sync for CLI operations."""
    # Replace asyncpg with psycopg2 for synchronous operations
    if "+asyncpg" in database_url:
        return database_url.replace("+asyncpg", "")
    return database_url


# Create synchronous database engine for CLI and non-async operations
sync_url = get_sync_database_url(settings.database_url)
engine = create_engine(
    sync_url,
    pool_pre_ping=True,  # Verify connections before using
    pool_size=10,  # Maximum number of connections
    max_overflow=20,  # Maximum overflow connections
    echo=settings.debug,  # Log SQL queries in debug mode
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for getting database session.

    Usage in FastAPI endpoints:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize database tables."""
    # Import all models to ensure they're registered with Base
    from models import (
        Base, User, Session, Chat, EmailVerification,  # noqa
        FCMDevice, Threat, PromoCode, PaymeTransaction  # noqa
    )

    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


def drop_db() -> None:
    """Drop all database tables (use with caution!)."""
    # Import all models to ensure they're registered with Base
    from models import (
        Base, User, Session, Chat, EmailVerification,  # noqa
        FCMDevice, Threat, PromoCode, PaymeTransaction  # noqa
    )

    logger.warning("Dropping all database tables...")
    Base.metadata.drop_all(bind=engine)
    logger.warning("All database tables dropped")
