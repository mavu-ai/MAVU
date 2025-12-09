"""Inline keyboards for Telegram bot."""
from typing import Optional
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

from config import settings
from models.user import User


def get_language_keyboard() -> InlineKeyboardMarkup:
    """
    Get keyboard with language selection buttons.

    Returns:
        InlineKeyboardMarkup: Keyboard with language options
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="English",
                    callback_data="lang:en"
                ),
                InlineKeyboardButton(
                    text="Русский",
                    callback_data="lang:ru"
                ),
            ]
        ]
    )


def get_webapp_keyboard(user: Optional[User] = None) -> InlineKeyboardMarkup:
    """
    Get keyboard with Web App launch button.

    For registered users (with name/age/gender), includes session token in URL.
    For new/guest users, opens without session token.

    Args:
        user: User object (optional) for adding session token

    Returns:
        InlineKeyboardMarkup: Keyboard with Web App button
    """
    if not settings.telegram_webapp_url:
        # Fallback if Web App URL is not configured
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Configure Web App URL",
                        callback_data="config_needed"
                    )
                ]
            ]
        )

    # Build Web App URL
    webapp_url = settings.telegram_webapp_url

    # For registered users, create and append session token
    if user and user.is_registered:
        from services.session_service import SessionService
        from dependencies.database import SessionLocal

        try:
            db = SessionLocal()
            session_token = SessionService.create_session(
                db=db,
                user_id=user.id,
                expires_in_days=30  # 30-day session for convenience
            )
            db.close()

            # Append session token to URL
            separator = '&' if '?' in webapp_url else '?'
            webapp_url = f"{webapp_url}{separator}session_token={session_token}"
        except Exception as e:
            # If session creation fails, proceed without token
            import structlog
            logger = structlog.get_logger()
            logger.error("Failed to create session token for webapp", error=str(e))

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Launch MavuAI",
                    web_app=WebAppInfo(url=webapp_url)
                )
            ]
        ]
    )


def get_help_keyboard() -> InlineKeyboardMarkup:
    """
    Get keyboard with help options.

    Returns:
        InlineKeyboardMarkup: Keyboard with help buttons
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Launch MavuAI",
                    web_app=WebAppInfo(url=settings.telegram_webapp_url) if settings.telegram_webapp_url else None
                )
            ],
            [
                InlineKeyboardButton(
                    text="Support",
                    url="https://t.me/mavuai_support"  # Replace with your support channel
                )
            ]
        ]
    )
