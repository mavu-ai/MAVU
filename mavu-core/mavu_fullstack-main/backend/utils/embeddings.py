"""Embeddings generation using OpenAI."""
import openai
from typing import List, Optional
import structlog

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_not_exception_type

from config import settings

logger = structlog.get_logger()

# Initialize OpenAI client
client = openai.AsyncOpenAI(api_key=settings.openai_api_key)


class QuotaExceededError(Exception):
    """Raised when OpenAI quota is exceeded."""
    pass


class EmbeddingService:
    """Service for generating text embeddings with quota handling."""

    def __init__(self):
        self.model = settings.openai_embedding_model
        self.max_batch_size = 100
        self.quota_exceeded = False  # Track quota state

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_not_exception_type(QuotaExceededError)  # Don't retry on quota errors
    )
    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for a single text.

        Returns:
            List of floats representing the embedding, or None if quota exceeded
        """
        # If quota is known to be exceeded, fail fast
        if self.quota_exceeded:
            logger.warning("Skipping embedding generation - quota exceeded")
            return None

        try:
            response = await client.embeddings.create(
                model=self.model,
                input=text,
                encoding_format="float"
            )
            embedding = response.data[0].embedding
            logger.debug("Generated embedding", text_length=len(text))
            return embedding
        except openai.RateLimitError as e:
            # Check if it's a quota error (429)
            error_message = str(e).lower()
            if "quota" in error_message or "exceeded" in error_message:
                logger.error(
                    "OpenAI quota exceeded - embeddings disabled",
                    error=str(e),
                    message="RAG will continue without embeddings"
                )
                self.quota_exceeded = True
                raise QuotaExceededError("OpenAI quota exceeded") from e
            else:
                # Other rate limit errors (temporary) - can retry
                logger.warning("Rate limit hit, will retry", error=str(e))
                raise
        except Exception as e:
            logger.error("Failed to generate embedding", error=str(e), error_type=type(e).__name__)
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_not_exception_type(QuotaExceededError)
    )
    async def generate_embeddings_batch(
            self, texts: List[str]
    ) -> Optional[List[List[float]]]:
        """
        Generate embeddings for multiple texts in batch.

        Returns:
            List of embeddings, or None if quota exceeded
        """
        # If quota is known to be exceeded, fail fast
        if self.quota_exceeded:
            logger.warning("Skipping batch embedding generation - quota exceeded")
            return None

        try:
            # Process in batches if necessary
            if len(texts) > self.max_batch_size:
                embeddings = []
                for i in range(0, len(texts), self.max_batch_size):
                    batch = texts[i:i + self.max_batch_size]
                    response = await client.embeddings.create(
                        model=self.model,
                        input=batch,
                        encoding_format="float"
                    )
                    batch_embeddings = [item.embedding for item in response.data]
                    embeddings.extend(batch_embeddings)
                logger.info(f"Generated {len(embeddings)} embeddings in batches")
                return embeddings
            else:
                response = await client.embeddings.create(
                    model=self.model,
                    input=texts,
                    encoding_format="float"
                )
                embeddings = [item.embedding for item in response.data]
                logger.info(f"Generated {len(embeddings)} embeddings")
                return embeddings
        except openai.RateLimitError as e:
            # Check if it's a quota error (429)
            error_message = str(e).lower()
            if "quota" in error_message or "exceeded" in error_message:
                logger.error(
                    "OpenAI quota exceeded - batch embeddings disabled",
                    error=str(e),
                    message="RAG will continue without embeddings"
                )
                self.quota_exceeded = True
                raise QuotaExceededError("OpenAI quota exceeded") from e
            else:
                logger.warning("Rate limit hit on batch, will retry", error=str(e))
                raise
        except Exception as e:
            logger.error("Failed to generate batch embeddings", error=str(e), error_type=type(e).__name__)
            raise

    async def generate_query_embedding(self, query: str) -> Optional[List[float]]:
        """
        Generate embedding optimized for search queries.

        Returns:
            Embedding vector, or None if quota exceeded
        """
        # Add query prefix for better retrieval
        query_text = f"search query: {query}"
        return await self.generate_embedding(query_text)

    def reset_quota_flag(self):
        """Reset the quota exceeded flag (for testing or after quota renewal)."""
        self.quota_exceeded = False
        logger.info("Quota exceeded flag reset")


# Global embedding service instance
embedding_service = EmbeddingService()
