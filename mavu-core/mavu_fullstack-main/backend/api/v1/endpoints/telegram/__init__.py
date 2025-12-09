"""Telegram bot webhook and Web App endpoints."""
from .router import router
from .bot import bot, dp, get_bot, get_dispatcher
from .webhook import setup_webhook, remove_webhook, process_update

__all__ = [
    "router",
    "bot",
    "dp",
    "get_bot",
    "get_dispatcher",
    "setup_webhook",
    "remove_webhook",
    "process_update",
]
