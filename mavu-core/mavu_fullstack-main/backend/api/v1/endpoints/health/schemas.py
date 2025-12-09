"""Health and debug schemas."""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    environment: str
    timestamp: datetime


class EmbeddingTestRequest(BaseModel):
    """Embedding test request."""
    text: str


class EmbeddingTestResponse(BaseModel):
    """Embedding test response."""
    text: str
    embedding_dim: int
    first_10: List[float]


class RAGTestRequest(BaseModel):
    """RAG test request."""
    query: str
    user_id: str = "test_user"


class RAGTestResponse(BaseModel):
    """RAG test response."""
    query: str
    user_id: str
    context: dict
