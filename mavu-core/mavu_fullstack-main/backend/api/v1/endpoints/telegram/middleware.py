"""Custom middleware for Telegram bot."""
from typing import Callable, Dict, Any, Awaitable
import structlog

from aiogram import BaseMiddleware
from aiogram.types import Update, TelegramObject

logger = structlog.get_logger()


class LoggingMiddleware(BaseMiddleware):
    """
    Middleware for logging all updates.

    Logs incoming updates with user information for debugging and monitoring.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """Process update and log information."""
        update: Update = data.get("event_update")

        if update:
            # Extract user information
            user = None
            if update.message:
                user = update.message.from_user
            elif update.callback_query:
                user = update.callback_query.from_user

            # Log the update
            logger.info(
                "Received Telegram update",
                update_id=update.update_id,
                user_id=user.id if user else None,
                username=user.username if user else None,
                update_type=update.event_type if hasattr(update, 'event_type') else None
            )

        # Call the handler
        try:
            result = await handler(event, data)
            return result
        except Exception as e:
            logger.error(
                "Error processing update",
                error=str(e),
                update_id=update.update_id if update else None
            )
            raise


class SecurityMiddleware(BaseMiddleware):
    """
    Middleware for security checks.

    Performs basic security validations on incoming updates.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """Process update and perform security checks."""
        update: Update = data.get("event_update")

        if update:
            # You can add custom security checks here
            # For example: rate limiting, banned users, etc.
            pass

        # Call the handler
        return await handler(event, data)


class ErrorHandlerMiddleware(BaseMiddleware):
    """
    Middleware for centralized error handling.

    Catches and logs errors, preventing bot crashes.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """Process update with error handling."""
        try:
            return await handler(event, data)
        except Exception as e:
            update: Update = data.get("event_update")

            logger.error(
                "Unhandled error in bot handler",
                error=str(e),
                error_type=type(e).__name__,
                update_id=update.update_id if update else None
            )

            # Try to notify user about the error
            if update and update.message:
                try:
                    await update.message.answer(
                        "Sorry, an error occurred while processing your request. "
                        "Please try again later."
                    )
                except Exception:
                    # If we can't send a message, just log and continue
                    pass

            # Don't re-raise to prevent bot from stopping
            return None
