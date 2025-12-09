"""Telegram bot webhook and Web App endpoints."""
import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, Header, status
from sqlalchemy.orm import Session

from dependencies.database import get_db
from dependencies.auth import get_or_create_user_from_telegram_id
from services.user_cache import get_user_cache
from utils.telegram import validate_telegram_webapp_request
from config import settings
from .schemas import (
    TelegramAuthRequest,
    TelegramAuthResponse,
    WebhookInfo,
    WebhookSetupResponse
)

logger = structlog.get_logger()
router = APIRouter()


@router.post("/webhook")
async def telegram_webhook(
        request: Request,
        x_telegram_bot_api_secret_token: str = Header(None)
):
    """
    Webhook endpoint for receiving Telegram bot updates.

    This endpoint receives updates from Telegram when users interact with the bot.
    It validates the secret token and processes updates through the bot dispatcher.

    Security:
        - Validates X-Telegram-Bot-Api-Secret-Token header
        - Only accepts updates from Telegram servers

    Note:
        This endpoint must be registered with Telegram using the setWebhook method.
    """
    # Validate secret token if configured
    if settings.telegram_webhook_secret:
        if not x_telegram_bot_api_secret_token:
            logger.warning("Webhook request without secret token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing secret token"
            )

        if x_telegram_bot_api_secret_token != settings.telegram_webhook_secret:
            logger.warning("Webhook request with invalid secret token")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid secret token"
            )

    try:
        # Get update data
        update_data = await request.json()

        # Process update through bot dispatcher
        from .webhook import process_update
        await process_update(update_data)

        logger.debug("Webhook update processed", update_id=update_data.get("update_id"))

        return {"ok": True}

    except Exception as e:
        logger.error("Error processing webhook update", error=str(e))
        # Return 200 even on error to prevent Telegram from retrying
        return {"ok": False, "error": str(e)}


@router.post("/webhook/setup", response_model=WebhookSetupResponse)
async def setup_telegram_webhook():
    """
    Set up webhook for Telegram bot.

    This endpoint configures the bot to receive updates via webhook instead of polling.
    Should be called once during deployment or when webhook URL changes.

    Requirements:
        - TELEGRAM_WEBHOOK_URL must be configured in settings
        - URL must be HTTPS in production
        - URL must be publicly accessible

    Returns:
        WebhookSetupResponse with setup status and webhook information
    """
    if not settings.telegram_bot_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Telegram bot token not configured"
        )

    if not settings.telegram_webhook_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Telegram webhook URL not configured"
        )

    try:
        from .webhook import setup_webhook
        from .bot import bot

        # Setup webhook
        success = await setup_webhook()

        # Get webhook info
        webhook_info = await bot.get_webhook_info()

        webhook_info_data = WebhookInfo(
            url=webhook_info.url,
            has_custom_certificate=webhook_info.has_custom_certificate,
            pending_update_count=webhook_info.pending_update_count,
            last_error_date=webhook_info.last_error_date,
            last_error_message=webhook_info.last_error_message
        )

        return WebhookSetupResponse(
            success=success,
            message="Webhook configured successfully" if success else "Failed to configure webhook",
            webhook_info=webhook_info_data
        )

    except Exception as e:
        logger.error("Error setting up webhook", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to setup webhook: {str(e)}"
        )


@router.get("/webhook/info", response_model=WebhookInfo)
async def get_webhook_info():
    """
    Get current webhook information.

    Returns details about the configured webhook including URL, status, and any errors.
    """
    if not settings.telegram_bot_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Telegram bot token not configured"
        )

    try:
        from .bot import bot

        webhook_info = await bot.get_webhook_info()

        return WebhookInfo(
            url=webhook_info.url,
            has_custom_certificate=webhook_info.has_custom_certificate,
            pending_update_count=webhook_info.pending_update_count,
            last_error_date=webhook_info.last_error_date,
            last_error_message=webhook_info.last_error_message
        )

    except Exception as e:
        logger.error("Error getting webhook info", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get webhook info: {str(e)}"
        )


@router.post("/auth", response_model=TelegramAuthResponse)
async def telegram_auth(
        request_data: TelegramAuthRequest,
        db: Session = Depends(get_db)
):
    """
    Authenticate Telegram Web App user.

    This endpoint validates Telegram initData and returns user information.
    Users are auto-registered if they don't exist (Telegram users are pre-verified).

    Flow:
        1. Validate Telegram initData signature
        2. Extract telegram_id and user info
        3. Get or create user by telegram_id
        4. Update language preference if provided
        5. Return user data (NO session token - Telegram handles auth)

    Args:
        request_data: Telegram authentication request with initData
        db: Database session

    Returns:
        TelegramAuthResponse with user_id, telegram_id, and language

    Note:
        Telegram Web App users don't need session tokens.
        They authenticate via X-Telegram-Init-Data header in subsequent requests.
    """
    # Validate Telegram initData
    is_valid, user_info = validate_telegram_webapp_request(request_data.init_data)

    if not is_valid or not user_info:
        logger.warning("Invalid Telegram initData provided")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Telegram authentication data"
        )

    telegram_id = user_info.get('telegram_id')
    if not telegram_id:
        logger.warning("No telegram_id in validated initData")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing telegram_id in authentication data"
        )

    try:
        # Get or create user from telegram_id
        user = get_or_create_user_from_telegram_id(telegram_id, user_info, db)

        # Update language preference if provided
        if request_data.language and user.language != request_data.language:
            user.language = request_data.language
            db.commit()
            db.refresh(user)
            logger.info(
                "Updated user language preference",
                user_id=user.id,
                language=request_data.language
            )

        # Invalidate cache
        cache = get_user_cache()
        cache.invalidate(user.id)

        logger.info(
            "Telegram user authenticated successfully",
            user_id=user.id,
            telegram_id=telegram_id,
            language=user.language
        )

        return TelegramAuthResponse(
            user_id=str(user.id),  # Return database ID as string
            telegram_id=user.telegram_id,
            language=user.language,
            username=user.username,
            name=user.name
        )

    except Exception as e:
        logger.error("Error authenticating Telegram user", error=str(e))
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to authenticate Telegram user"
        )
