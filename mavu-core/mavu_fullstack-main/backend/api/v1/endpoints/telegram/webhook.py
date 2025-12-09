"""Webhook setup and management for Telegram bot."""
import asyncio
import structlog
from aiogram.types import Update
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from aiogram.exceptions import TelegramRetryAfter

from config import settings
from .bot import bot, dp
from .handlers import router
from .middleware import LoggingMiddleware, SecurityMiddleware, ErrorHandlerMiddleware

logger = structlog.get_logger()

# Register handlers router and middleware only if dispatcher is available
if dp:
    dp.include_router(router)

    # Register middleware (order matters - first added is executed first)
    dp.update.middleware(LoggingMiddleware())
    dp.update.middleware(SecurityMiddleware())
    dp.update.middleware(ErrorHandlerMiddleware())


async def setup_webhook(max_retries: int = 3) -> bool:
    """
    Set up webhook for the bot with retry logic for rate limits.

    Args:
        max_retries: Maximum number of retry attempts

    Returns:
        bool: True if webhook was set successfully, False otherwise
    """
    if not settings.telegram_bot_token:
        logger.error("Telegram bot token not configured")
        return False

    if not settings.telegram_webhook_url:
        logger.warning("Telegram webhook URL not configured, skipping webhook setup")
        return False

    for attempt in range(max_retries):
        try:
            # Get current webhook info
            webhook_info = await bot.get_webhook_info()

            # If webhook is already set to the correct URL, skip
            if webhook_info.url == settings.telegram_webhook_url:
                logger.info("Webhook already configured correctly", url=webhook_info.url)
                return True

            logger.info(
                "Current webhook info",
                url=webhook_info.url,
                pending_update_count=webhook_info.pending_update_count,
                attempt=attempt + 1
            )

            # Set webhook with optional secret token for security
            webhook_url = settings.telegram_webhook_url
            secret_token = settings.telegram_webhook_secret

            await bot.set_webhook(
                url=webhook_url,
                secret_token=secret_token,
                allowed_updates=dp.resolve_used_update_types(),
                drop_pending_updates=True  # Drop old updates on restart
            )

            # Verify webhook was set
            webhook_info = await bot.get_webhook_info()
            logger.info(
                "Webhook configured successfully",
                url=webhook_info.url,
                has_custom_certificate=webhook_info.has_custom_certificate,
                pending_update_count=webhook_info.pending_update_count
            )

            return True

        except TelegramRetryAfter as e:
            retry_after = e.retry_after if hasattr(e, 'retry_after') else 5
            logger.warning(
                "Rate limit hit, retrying",
                retry_after=retry_after,
                attempt=attempt + 1,
                max_retries=max_retries
            )
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_after)
            else:
                logger.error("Max retries reached for webhook setup")
                return False

        except Exception as e:
            logger.error("Failed to set up webhook", error=str(e), attempt=attempt + 1)
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            else:
                return False

    return False


async def remove_webhook() -> bool:
    """
    Remove webhook from the bot.

    Returns:
        bool: True if webhook was removed successfully, False otherwise
    """
    if not settings.telegram_bot_token:
        logger.error("Telegram bot token not configured")
        return False

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Webhook removed successfully")
        return True

    except Exception as e:
        logger.error("Failed to remove webhook", error=str(e))
        return False


async def process_update(update_data: dict) -> None:
    """
    Process incoming webhook update.

    Args:
        update_data: Raw update data from Telegram

    Raises:
        Exception: If update processing fails
    """
    try:
        # Parse update
        update = Update(**update_data)

        # Process update through dispatcher
        await dp.feed_update(bot=bot, update=update)

        logger.debug("Update processed successfully", update_id=update.update_id)

    except Exception as e:
        logger.error(
            "Error processing update",
            error=str(e),
            update_data=update_data
        )
        raise


def get_webhook_handler():
    """
    Get webhook request handler for aiohttp.

    This is an alternative approach if needed, but we'll use manual processing
    in FastAPI for better integration.

    Returns:
        SimpleRequestHandler: Handler for aiohttp
    """
    return SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=settings.telegram_webhook_secret
    )
