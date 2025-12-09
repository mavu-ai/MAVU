"""WebSocket message schemas."""
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class WebSocketMessage(BaseModel):
    """WebSocket message format."""
    type: str
    data: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None


class AudioAppendMessage(BaseModel):
    """Audio append message."""
    type: str = "audio.append"
    audio: str  # base64 encoded


class AudioCommitMessage(BaseModel):
    """Audio commit message."""
    type: str = "audio.commit"


class TextInputMessage(BaseModel):
    """Text input message."""
    type: str = "text.input"
    text: str


class ErrorMessage(BaseModel):
    """Error message."""
    type: str = "error"
    error: str
    detail: Optional[str] = None
