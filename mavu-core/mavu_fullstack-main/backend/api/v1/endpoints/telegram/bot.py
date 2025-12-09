"""Telegram bot initialization with aiogram best practices."""
import structlog
from typing import Optional
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import settings

logger = structlog.get_logger()

# Global instances (initialized lazily)
_bot: Optional[Bot] = None
_dp: Optional[Dispatcher] = None
_storage: Optional[MemoryStorage] = None


def get_bot() -> Bot:
    """Get or create bot instance."""
    global _bot
    if _bot is None:
        if not settings.telegram_bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN not configured")
        _bot = Bot(
            token=settings.telegram_bot_token,
            default=DefaultBotProperties(
                parse_mode=ParseMode.HTML,
                link_preview_is_disabled=True
            )
        )
    return _bot


def get_dispatcher() -> Dispatcher:
    """Get or create dispatcher instance."""
    global _dp, _storage
    if _dp is None:
        _storage = MemoryStorage()
        _dp = Dispatcher(storage=_storage)
    return _dp


# Create instances if token is configured
if settings.telegram_bot_token:
    bot = get_bot()
    dp = get_dispatcher()
    storage = _storage
else:
    # Create placeholder objects that will raise error if used
    bot = None  # type: ignore
    dp = None  # type: ignore
    storage = None  # type: ignore


async def on_startup():
    """Execute on bot startup."""
    logger.info("Telegram bot starting up")

    # Set bot commands
    from aiogram.types import BotCommand, BotCommandScopeDefault

    commands = [
        BotCommand(command="start", description="Start the bot and launch MavuAI Web App"),
        BotCommand(command="help", description="Show help information"),
    ]

    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())
    logger.info("Bot commands configured", commands=[cmd.command for cmd in commands])


async def on_shutdown():
    """Execute on bot shutdown."""
    if not bot or not storage:
        return

    logger.info("Telegram bot shutting down")

    # Close bot session
    await bot.session.close()

    # Close storage
    await storage.close()

    logger.info("Telegram bot shutdown complete")


# Register startup and shutdown handlers
if dp:
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
