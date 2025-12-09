"""Health and debug router."""
from datetime import datetime
from fastapi import APIRouter, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
import structlog

from config import settings
from utils.weaviate_client import weaviate_client
from .schemas import HealthCheckResponse, EmbeddingTestRequest, RAGTestRequest

logger = structlog.get_logger()

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.get("/", response_model=HealthCheckResponse)
async def health_check():
    """
    Basic health check endpoint.

    Returns:
        HealthCheckResponse with current status, version, and timestamp
    """
    # Check Weaviate connection
    weaviate_status = "connected" if weaviate_client.client else "disconnected"

    return HealthCheckResponse(
        status=weaviate_status,
        version=settings.app_version,
        environment=settings.environment,
        timestamp=datetime.utcnow()
    )


@router.post("/embedding")
@limiter.limit("10/minute")
async def test_embedding(request: Request, data: dict):
    """
    Test embedding generation endpoint (for debugging).

    Rate limited to 10 requests per minute.

    Args:
        data: Dictionary with "text" key containing the text to embed

    Returns:
        Dictionary with embedding information
    """
    from utils.embeddings import embedding_service

    text = data.get("text", "")
    if not text:
        return {"error": "Text is required"}

    try:
        embedding = await embedding_service.generate_embedding(text)
        return {
            "text": text,
            "embedding_dim": len(embedding),
            "first_10": embedding[:10] if len(embedding) >= 10 else embedding
        }
    except Exception as e:
        logger.error("Embedding test failed", error=str(e))
        return {"error": str(e)}


@router.post("/rag")
@limiter.limit("10/minute")
async def test_rag(request: Request, data: dict):
    """
    Test RAG retrieval endpoint (for debugging).

    Rate limited to 10 requests per minute.

    Args:
        data: Dictionary with "query" and optional "user_id"

    Returns:
        RAG context retrieval results
    """
    from rag.pipeline import rag_pipeline

    query = data.get("query", "")
    user_id = data.get("user_id", "test_user")

    if not query:
        return {"error": "Query is required"}

    try:
        context = await rag_pipeline.retrieve_context(
            query=query,
            owner_id=user_id
        )
        return context
    except Exception as e:
        logger.error("RAG test failed", error=str(e))
        return {"error": str(e)}
