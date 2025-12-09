"""Real-time WebSocket router."""
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from datetime import datetime
import structlog
import uuid

from dependencies.auth import get_user_id_from_websocket
from realtime.websocket_handler import RealtimeStreamHandler
from dependencies.database import get_db

logger = structlog.get_logger()

router = APIRouter()


@router.websocket("")
async def realtime_websocket(
    websocket: WebSocket,
    user_id: str = Depends(get_user_id_from_websocket),
    db: Session = Depends(get_db)
):
    """
    🎙️ Real-Time Voice Chat WebSocket - Mobile Compatible

    ## Overview
    Connect to this endpoint for real-time bidirectional voice conversations with AI assistant.
    Features automatic RAG context injection for intelligent, context-aware responses.

    ## Connection URL
    ```
    Production: wss://mavu-api.aey-inc.uz/api/v1/realtime?session_token=YOUR_TOKEN
    Development: ws://localhost:8000/api/v1/realtime?session_token=YOUR_TOKEN
    ```

    ## Authentication Methods

    ### Method 1: Query Parameter (Recommended for Mobile)
    ```
    ws://mavu-api.aey-inc.uz/api/v1/realtime?session_token=abc123xyz
    ```

    ### Method 2: HTTP Headers
    ```
    X-Session-Token: abc123xyz
    # OR
    Authorization: Bearer abc123xyz
    ```

    ### Method 3: Development Only
    ```
    ws://localhost:8000/api/v1/realtime?user_id=123
    ```

    ## Audio Format
    - **Encoding:** PCM16 (signed 16-bit little-endian)
    - **Sample Rate:** 24000 Hz
    - **Channels:** Mono (1 channel)
    - **Transport:** Base64-encoded in JSON messages

    ## Message Protocol

    ### Client → Server

    **Audio Input:**
    ```json
    {
      "type": "audio",
      "audio": "BASE64_ENCODED_PCM16_AUDIO"
    }
    ```

    **Refresh Context:**
    ```json
    {
      "type": "refresh_context"
    }
    ```

    ### Server → Client

    **Session Ready:**
    ```json
    {
      "type": "session.ready",
      "session_id": "uuid-here",
      "user_id": "123"
    }
    ```

    **Audio Response:**
    ```json
    {
      "type": "audio",
      "audio": "BASE64_ENCODED_PCM16_AUDIO"
    }
    ```

    **Transcript:**
    ```json
    {
      "type": "transcript",
      "text": "User's spoken text",
      "role": "user"
    }
    ```

    **RAG Context Update:**
    ```json
    {
      "type": "context.updated",
      "user_context": [...],
      "app_context": [...],
      "retrieval_method": "hybrid",
      "query": "..."
    }
    ```

    **Error:**
    ```json
    {
      "type": "error",
      "error": "Error description"
    }
    ```

    ## Mobile Platform Examples

    ### iOS (Swift)
    ```swift
    import Foundation

    let url = URL(string: "wss://mavu-api.aey-inc.uz/api/v1/realtime?session_token=TOKEN")!
    let session = URLSession(configuration: .default)
    let webSocket = session.webSocketTask(with: url)
    webSocket.resume()
    ```

    ### Android (Kotlin)
    ```kotlin
    import okhttp3.OkHttpClient
    import okhttp3.Request

    val client = OkHttpClient()
    val request = Request.Builder()
        .url("wss://mavu-api.aey-inc.uz/api/v1/realtime?session_token=TOKEN")
        .build()
    val webSocket = client.newWebSocket(request, listener)
    ```

    ## Features
    - ✅ Real-time speech-to-speech communication
    - ✅ Automatic voice activity detection (VAD)
    - ✅ Context-aware responses using RAG
    - ✅ Automatic chat history persistence
    - ✅ Multi-language support (English, Russian, etc.)
    - ✅ Character skins with different voices (Alex, Maya, Robo)

    ## Error Handling

    **WebSocket Close Codes:**
    - `1000` - Normal closure
    - `1008` - Authentication failed
    - `1011` - Internal server error

    ## Performance Notes
    - **Recommended buffer size:** 2048-4096 samples for low latency
    - **Expected latency:** 100-200ms (network + processing)
    - **Max connection duration:** Unlimited (auto-reconnect recommended)

    ## Rate Limits
    - **Connections:** No limit per user
    - **Audio data:** No size limits (streaming)
    - **Messages:** 1000/minute per session

    ## Testing
    Use `wscat` for testing:
    ```bash
    npm install -g wscat
    wscat -c "ws://localhost:8000/api/v1/realtime?session_token=TOKEN"
    ```

    ## Support
    - 📧 Email: support@mavu.app

    ---

    **Args:**
        websocket: WebSocket connection
        user_id_result: Authenticated user ID from dependency
        db: Database session for saving chat history
    """
    # Generate unique handler ID for debugging
    handler_id = f"handler-{uuid.uuid4().hex[:8]}"

    logger.info("WebSocket connection initiated",
                user_id=user_id,
                handler_id=handler_id,
                timestamp=datetime.now().isoformat())

    # FEATURE: Pass database session to handler for chat history
    handler = RealtimeStreamHandler(websocket, user_id, db)

    try:
        await handler.start()
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected", user_id=user_id)
        await handler.cleanup()
    except Exception as e:
        logger.error("WebSocket error", user_id=user_id, error=str(e))
        await handler.cleanup()
