"""Redis client for caching and chat history."""
import json
from typing import Any, Dict, List, Optional
import redis.asyncio as redis
import structlog

from config import settings

logger = structlog.get_logger()


class RedisClient:
    """Async Redis client for caching and chat history."""

    def __init__(self):
        self.client: Optional[redis.Redis] = None
        self.connected = False

    async def connect(self):
        """Connect to Redis."""
        try:
            self.client = await redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            # Test connection
            await self.client.ping()
            self.connected = True
            logger.info("Redis connected successfully", url=settings.redis_url)
        except Exception as e:
            logger.warning("Failed to connect to Redis, will operate without cache", error=str(e))
            self.connected = False
            self.client = None

    async def disconnect(self):
        """Disconnect from Redis."""
        if self.client:
            try:
                await self.client.aclose()
                logger.info("Redis disconnected")
            except Exception as e:
                logger.error("Error disconnecting from Redis", error=str(e))
            finally:
                self.client = None
                self.connected = False

    async def get(self, key: str) -> Optional[str]:
        """Get value from Redis."""
        if not self.connected or not self.client:
            return None
        try:
            return await self.client.get(key)
        except Exception as e:
            logger.error("Redis GET error", key=key, error=str(e))
            return None

    async def set(self, key: str, value: str, ttl: Optional[int] = None):
        """Set value in Redis with optional TTL."""
        if not self.connected or not self.client:
            return False
        try:
            if ttl:
                await self.client.setex(key, ttl, value)
            else:
                await self.client.set(key, value)
            return True
        except Exception as e:
            logger.error("Redis SET error", key=key, error=str(e))
            return False

    async def delete(self, key: str):
        """Delete key from Redis."""
        if not self.connected or not self.client:
            return False
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.error("Redis DELETE error", key=key, error=str(e))
            return False

    # Chat history specific methods
    async def add_voice_chat(self, user_id: str, role: str, message: str, timestamp: str):
        """
        Add a voice chat message to Redis history.
        Keeps last 10 chats per user.

        Args:
            user_id: User ID
            role: "user" or "assistant"
            message: The message content
            timestamp: ISO timestamp
        """
        if not self.connected or not self.client:
            return False

        try:
            key = f"user:{user_id}:voice_chats"

            # Create chat entry
            chat_entry = json.dumps({
                "role": role,
                "message": message,
                "timestamp": timestamp
            })

            # Add to list (left push for newest first)
            await self.client.lpush(key, chat_entry)

            # Keep only last 20 entries (10 conversations = user + assistant)
            await self.client.ltrim(key, 0, 19)

            logger.debug("Voice chat added to Redis", user_id=user_id, role=role)
            return True
        except Exception as e:
            logger.error("Failed to add voice chat to Redis", user_id=user_id, error=str(e))
            return False

    async def get_recent_voice_chats(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent voice chats for a user.

        Args:
            user_id: User ID
            limit: Number of chat pairs to retrieve (default 10)

        Returns:
            List of chat messages in chronological order (oldest first)
        """
        if not self.connected or not self.client:
            return []

        try:
            key = f"user:{user_id}:voice_chats"

            # Get last N entries (limit * 2 for user + assistant pairs)
            entries = await self.client.lrange(key, 0, (limit * 2) - 1)

            # Parse JSON entries
            chats = []
            for entry in entries:
                try:
                    chats.append(json.loads(entry))
                except json.JSONDecodeError:
                    logger.warning("Invalid JSON in chat history", entry=entry)
                    continue

            # Reverse to get chronological order (oldest first)
            chats.reverse()

            logger.debug("Retrieved voice chats from Redis", user_id=user_id, count=len(chats))
            return chats
        except Exception as e:
            logger.error("Failed to get voice chats from Redis", user_id=user_id, error=str(e))
            return []

    async def clear_voice_chats(self, user_id: str):
        """Clear voice chat history for a user."""
        if not self.connected or not self.client:
            return False
        try:
            key = f"user:{user_id}:voice_chats"
            await self.client.delete(key)
            logger.info("Cleared voice chats from Redis", user_id=user_id)
            return True
        except Exception as e:
            logger.error("Failed to clear voice chats", user_id=user_id, error=str(e))
            return False


# Global Redis client instance
redis_client = RedisClient()
