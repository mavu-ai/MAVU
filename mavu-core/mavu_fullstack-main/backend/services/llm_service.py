"""Service for LLM chat completions using OpenAI."""
import time
from typing import Dict, List, Optional
import structlog

from openai import AsyncOpenAI

from config import settings

logger = structlog.get_logger()


class LLMService:
    """Service for generating chat completions using OpenAI."""

    _client: AsyncOpenAI = None

    @classmethod
    def get_client(cls) -> AsyncOpenAI:
        """Get or create OpenAI client for chat completions."""
        if cls._client is None:
            cls._client = AsyncOpenAI(
                api_key=settings.openai_api_key
            )
        return cls._client

    @classmethod
    async def generate_response(
        cls,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> tuple[str, float]:
        """
        Generate chat completion response.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate

        Returns:
            Tuple of (response text, latency in seconds)
        """
        client = cls.get_client()
        start_time = time.time()

        try:
            kwargs = {
                "model": settings.openai_chat_model,  # Use chat model, not realtime model
                "messages": messages,
                "temperature": temperature
            }

            if max_tokens:
                kwargs["max_tokens"] = max_tokens

            response = await client.chat.completions.create(**kwargs)

            latency = time.time() - start_time
            response_text = response.choices[0].message.content

            logger.info("Generated LLM response", latency=f"{latency:.3f}s")
            return response_text, latency

        except Exception as e:
            latency = time.time() - start_time
            logger.error("Error generating LLM response", latency=f"{latency:.3f}s", error=str(e))
            raise

    @classmethod
    async def generate_streaming_response(
        cls,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ):
        """
        Generate streaming chat completion response.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate

        Yields:
            Response chunks as they arrive
        """
        client = cls.get_client()
        start_time = time.time()

        try:
            kwargs = {
                "model": settings.openai_chat_model,  # Use chat model, not realtime model
                "messages": messages,
                "temperature": temperature,
                "stream": True
            }

            if max_tokens:
                kwargs["max_tokens"] = max_tokens

            stream = await client.chat.completions.create(**kwargs)

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

            latency = time.time() - start_time
            logger.info("Completed streaming LLM response", latency=f"{latency:.3f}s")

        except Exception as e:
            latency = time.time() - start_time
            logger.error("Error in streaming LLM response", latency=f"{latency:.3f}s", error=str(e))
            raise
