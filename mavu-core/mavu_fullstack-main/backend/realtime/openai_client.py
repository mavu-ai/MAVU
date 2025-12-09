"""OpenAI Realtime API WebSocket client for speech-to-speech."""
import json
import asyncio
import websockets
import base64
from typing import Dict, Any, Optional, Callable, List
import structlog
from dataclasses import dataclass
from enum import Enum

from config import settings

logger = structlog.get_logger()


class RealtimeEventType(Enum):
    """OpenAI Realtime API event types."""
    # Client events
    SESSION_UPDATE = "session.update"
    INPUT_AUDIO_BUFFER_APPEND = "input_audio_buffer.append"
    INPUT_AUDIO_BUFFER_COMMIT = "input_audio_buffer.commit"
    INPUT_AUDIO_BUFFER_CLEAR = "input_audio_buffer.clear"
    CONVERSATION_ITEM_CREATE = "conversation.item.create"
    CONVERSATION_ITEM_TRUNCATE = "conversation.item.truncate"
    CONVERSATION_ITEM_DELETE = "conversation.item.delete"
    RESPONSE_CREATE = "response.create"
    RESPONSE_CANCEL = "response.cancel"

    # Server events
    ERROR = "error"
    SESSION_CREATED = "session.created"
    SESSION_UPDATED = "session.updated"
    CONVERSATION_CREATED = "conversation.created"
    INPUT_AUDIO_BUFFER_COMMITTED = "input_audio_buffer.committed"
    INPUT_AUDIO_BUFFER_CLEARED = "input_audio_buffer.cleared"
    INPUT_AUDIO_BUFFER_SPEECH_STARTED = "input_audio_buffer.speech_started"
    INPUT_AUDIO_BUFFER_SPEECH_STOPPED = "input_audio_buffer.speech_stopped"
    CONVERSATION_ITEM_CREATED = "conversation.item.created"
    CONVERSATION_ITEM_INPUT_AUDIO_TRANSCRIPTION_COMPLETED = "conversation.item.input_audio_transcription.completed"
    CONVERSATION_ITEM_INPUT_AUDIO_TRANSCRIPTION_FAILED = "conversation.item.input_audio_transcription.failed"
    CONVERSATION_ITEM_TRUNCATED = "conversation.item.truncated"
    CONVERSATION_ITEM_DELETED = "conversation.item.deleted"
    RESPONSE_CREATED = "response.created"
    RESPONSE_DONE = "response.done"
    RESPONSE_OUTPUT_ITEM_ADDED = "response.output_item.added"
    RESPONSE_OUTPUT_ITEM_DONE = "response.output_item.done"
    RESPONSE_CONTENT_PART_ADDED = "response.content_part.added"
    RESPONSE_CONTENT_PART_DONE = "response.content_part.done"
    RESPONSE_TEXT_DELTA = "response.text.delta"
    RESPONSE_TEXT_DONE = "response.text.done"
    RESPONSE_AUDIO_TRANSCRIPT_DELTA = "response.audio_transcript.delta"
    RESPONSE_AUDIO_TRANSCRIPT_DONE = "response.audio_transcript.done"
    RESPONSE_AUDIO_DELTA = "response.audio.delta"
    RESPONSE_AUDIO_DONE = "response.audio.done"
    RESPONSE_FUNCTION_CALL_ARGUMENTS_DELTA = "response.function_call_arguments.delta"
    RESPONSE_FUNCTION_CALL_ARGUMENTS_DONE = "response.function_call_arguments.done"
    RATE_LIMITS_UPDATED = "rate_limits.updated"


@dataclass
class RealtimeSession:
    """Realtime session configuration."""
    id: Optional[str] = None
    model: str = "gpt-4o-realtime-preview"
    modalities: List[str] = None
    instructions: str = ""
    voice: str = "alloy"
    input_audio_format: str = "pcm16"
    output_audio_format: str = "pcm16"
    input_audio_transcription: Dict[str, Any] = None
    turn_detection: Dict[str, Any] = None
    tools: List[Dict[str, Any]] = None
    tool_choice: str = "auto"
    temperature: float = 0.8
    max_response_output_tokens: Optional[int] = None

    def __post_init__(self):
        if self.modalities is None:
            self.modalities = ["text", "audio"]
        if self.input_audio_transcription is None:
            self.input_audio_transcription = {"model": "whisper-1"}
        if self.turn_detection is None:
            self.turn_detection = {
                "type": "server_vad",
                "threshold": 0.5,
                "prefix_padding_ms": 300,
                "silence_duration_ms": 500
            }


class OpenAIRealtimeClient:
    """Client for OpenAI Realtime WebSocket API."""

    def __init__(
        self,
        api_key: str = None,
        model: str = None,
        on_transcription: Optional[Callable] = None,
        on_text_delta: Optional[Callable] = None,
        on_audio_delta: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
        on_buffer_committed: Optional[Callable] = None,
        on_response_done: Optional[Callable] = None
    ):
        self.api_key = api_key or settings.openai_api_key
        self.model = model or settings.openai_model
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.session: Optional[RealtimeSession] = None
        self.is_connected = False

        # Event handlers
        self.on_transcription = on_transcription
        self.on_text_delta = on_text_delta
        self.on_audio_delta = on_audio_delta
        self.on_error = on_error
        self.on_buffer_committed = on_buffer_committed
        self.on_response_done = on_response_done

        # Internal state
        self._response_text = ""
        self._response_audio = bytearray()
        self._input_transcript = ""
        self._event_queue = asyncio.Queue()
        self._handlers = {}
        self._setup_handlers()

    def _setup_handlers(self):
        """Setup event handlers for different message types."""
        self._handlers = {
            RealtimeEventType.ERROR.value: self._handle_error,
            RealtimeEventType.SESSION_CREATED.value: self._handle_session_created,
            RealtimeEventType.SESSION_UPDATED.value: self._handle_session_updated,
            RealtimeEventType.CONVERSATION_ITEM_INPUT_AUDIO_TRANSCRIPTION_COMPLETED.value: self._handle_transcription,
            RealtimeEventType.RESPONSE_TEXT_DELTA.value: self._handle_text_delta,
            RealtimeEventType.RESPONSE_TEXT_DONE.value: self._handle_text_done,
            RealtimeEventType.RESPONSE_AUDIO_DELTA.value: self._handle_audio_delta,
            RealtimeEventType.RESPONSE_AUDIO_DONE.value: self._handle_audio_done,
            RealtimeEventType.RESPONSE_AUDIO_TRANSCRIPT_DELTA.value: self._handle_audio_transcript_delta,
            RealtimeEventType.RESPONSE_DONE.value: self._handle_response_done,
            RealtimeEventType.INPUT_AUDIO_BUFFER_SPEECH_STARTED.value: self._handle_speech_started,
            RealtimeEventType.INPUT_AUDIO_BUFFER_SPEECH_STOPPED.value: self._handle_speech_stopped,
            RealtimeEventType.INPUT_AUDIO_BUFFER_COMMITTED.value: self._handle_buffer_committed,
        }

    async def connect(self, session_config: Optional[RealtimeSession] = None):
        """Connect to OpenAI Realtime WebSocket."""
        try:
            self.session = session_config or RealtimeSession(model=self.model)

            # Build WebSocket URL with model parameter
            ws_url = f"{settings.openai_realtime_url}?model={self.session.model}"

            # Connect with auth headers
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "OpenAI-Beta": "realtime=v1"
            }

            self.ws = await websockets.connect(
                ws_url,
                extra_headers=headers,
                ping_interval=20,
                ping_timeout=10
            )

            self.is_connected = True
            logger.info("Connected to OpenAI Realtime API", model=self.session.model)

            # Start message handler
            asyncio.create_task(self._message_handler())

            # Configure session
            await self._configure_session()

        except Exception as e:
            logger.error("Failed to connect to OpenAI Realtime", error=str(e))
            raise

    async def disconnect(self):
        """Disconnect from WebSocket."""
        if self.ws:
            await self.ws.close()
            self.ws = None
            self.is_connected = False
            logger.info("Disconnected from OpenAI Realtime")

    async def _configure_session(self):
        """Configure the realtime session."""
        session_update: dict[str, Any] = {
            "type": RealtimeEventType.SESSION_UPDATE.value,
            "session": {
                "modalities": self.session.modalities,
                "instructions": self.session.instructions,
                "voice": self.session.voice,
                "input_audio_format": self.session.input_audio_format,
                "output_audio_format": self.session.output_audio_format,
                "input_audio_transcription": self.session.input_audio_transcription,
                "turn_detection": self.session.turn_detection,
                "temperature": self.session.temperature,
            }
        }

        if self.session.tools:
            session_update["session"]["tools"] = self.session.tools
            session_update["session"]["tool_choice"] = self.session.tool_choice

        if self.session.max_response_output_tokens:
            session_update["session"]["max_response_output_tokens"] = self.session.max_response_output_tokens

        logger.info(
            "Configuring OpenAI session",
            modalities=self.session.modalities,
            voice=self.session.voice,
            input_format=self.session.input_audio_format,
            output_format=self.session.output_audio_format,
            turn_detection=self.session.turn_detection.get("type") if self.session.turn_detection else None
        )

        await self._send_event(session_update)

    async def _send_event(self, event: Dict[str, Any]):
        """Send an event to the WebSocket."""
        if not self.ws or not self.is_connected:
            logger.error("Cannot send event: not connected")
            return

        try:
            await self.ws.send(json.dumps(event))
            logger.debug("Sent event", event_type=event.get("type"))
        except Exception as e:
            logger.error("Failed to send event", error=str(e))
            raise

    async def _message_handler(self):
        """Handle incoming messages from WebSocket."""
        try:
            async for message in self.ws:
                try:
                    data = json.loads(message)
                    event_type = data.get("type")

                    # Log all events, with special attention to audio events
                    if event_type == RealtimeEventType.RESPONSE_AUDIO_DELTA.value:
                        audio_size = len(data.get("delta", ""))
                        logger.info("OpenAI audio event received", event_type=event_type, audio_size=audio_size)
                    elif event_type in [
                        RealtimeEventType.RESPONSE_AUDIO_DONE.value,
                        RealtimeEventType.RESPONSE_AUDIO_TRANSCRIPT_DELTA.value,
                        RealtimeEventType.RESPONSE_CREATED.value,
                        RealtimeEventType.RESPONSE_DONE.value
                    ]:
                        logger.info("OpenAI response event", event_type=event_type)
                    else:
                        logger.debug("Received event", event_type=event_type)

                    # Call specific handler if exists
                    handler = self._handlers.get(event_type)
                    if handler:
                        await handler(data)
                    else:
                        logger.debug("Unhandled event type", event_type=event_type)

                except json.JSONDecodeError as e:
                    logger.error("Failed to decode message", error=str(e))
                except Exception as e:
                    logger.error("Error handling message", error=str(e))

        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket connection closed")
            self.is_connected = False
        except Exception as e:
            logger.error("Message handler error", error=str(e))
            self.is_connected = False

    async def send_audio(self, audio_data: bytes):
        """Send audio data to the API."""
        # Convert to base64
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')

        event = {
            "type": RealtimeEventType.INPUT_AUDIO_BUFFER_APPEND.value,
            "audio": audio_base64
        }

        await self._send_event(event)

    async def commit_audio(self):
        """Commit the audio buffer for processing."""
        event = {
            "type": RealtimeEventType.INPUT_AUDIO_BUFFER_COMMIT.value
        }
        await self._send_event(event)

    async def clear_audio_buffer(self):
        """Clear the input audio buffer."""
        event = {
            "type": RealtimeEventType.INPUT_AUDIO_BUFFER_CLEAR.value
        }
        await self._send_event(event)

    async def send_text(self, text: str, role: str = "user"):
        """Send a text message."""
        event = {
            "type": RealtimeEventType.CONVERSATION_ITEM_CREATE.value,
            "item": {
                "type": "message",
                "role": role,
                "content": [
                    {
                        "type": "input_text",
                        "text": text
                    }
                ]
            }
        }
        await self._send_event(event)

    async def create_response(
        self,
        modalities: Optional[List[str]] = None,
        instructions: Optional[str] = None,
        temperature: Optional[float] = None
    ):
        """Create a response with optional overrides."""
        # Log response creation to detect duplicates
        logger.info(
            "Creating OpenAI response",
            modalities=modalities,
            has_instructions=bool(instructions),
            temperature=temperature
        )

        event = {
            "type": RealtimeEventType.RESPONSE_CREATE.value,
            "response": {}
        }

        if modalities:
            event["response"]["modalities"] = modalities
        if instructions:
            event["response"]["instructions"] = instructions
        if temperature is not None:
            event["response"]["temperature"] = temperature

        await self._send_event(event)

    async def cancel_response(self):
        """Cancel the current response."""
        event = {
            "type": RealtimeEventType.RESPONSE_CANCEL.value
        }
        await self._send_event(event)

    # Event handlers
    async def _handle_error(self, data: Dict[str, Any]):
        """Handle error events."""
        error = data.get("error", {})

        # CRITICAL FIX: Filter empty buffer errors - these are expected behavior
        # Don't log them as errors to avoid confusing developers
        error_code = error.get("code", "")
        error_message = str(error.get("message", ""))

        # Check if this is an expected buffer validation error
        if error_code == "input_audio_buffer_commit_empty" or \
           "buffer too small" in error_message.lower() or \
           "0.00ms" in error_message:
            # Log as INFO, not ERROR - this is expected when users click mic quickly
            logger.info(
                "OpenAI buffer validation (expected behavior)",
                error_code=error_code,
                error_message=error_message
            )
        else:
            # All other errors should be logged as errors
            logger.error("OpenAI Realtime error", error=error)

        # Always call the error handler callback (it will also filter appropriately)
        if self.on_error:
            await self.on_error(error)

    async def _handle_session_created(self, data: Dict[str, Any]):
        """Handle session created event."""
        session = data.get("session", {})
        self.session.id = session.get("id")
        logger.info("Session created", session_id=self.session.id)

    @staticmethod
    async def _handle_session_updated(data: Dict[str, Any]):
        """Handle session updated event."""
        logger.info("Session updated")

    async def _handle_transcription(self, data: Dict[str, Any]):
        """Handle input audio transcription."""
        transcript = data.get("transcript", "")
        self._input_transcript = transcript
        logger.info("Input transcription", transcript=transcript)
        if self.on_transcription:
            await self.on_transcription(transcript, "user")

    async def _handle_text_delta(self, data: Dict[str, Any]):
        """Handle text delta events."""
        delta = data.get("delta", "")
        self._response_text += delta
        if self.on_text_delta:
            await self.on_text_delta(delta)

    async def _handle_text_done(self, data: Dict[str, Any]):
        """Handle text done event."""
        text = data.get("text", "")
        logger.info("Text response complete", length=len(text))
        self._response_text = ""

    async def _handle_audio_delta(self, data: Dict[str, Any]):
        """Handle audio delta events."""
        audio_base64 = data.get("delta", "")
        if audio_base64:
            audio_bytes = base64.b64decode(audio_base64)
            self._response_audio.extend(audio_bytes)
            logger.info("Audio delta processed", bytes_count=len(audio_bytes), has_callback=bool(self.on_audio_delta))
            if self.on_audio_delta:
                await self.on_audio_delta(audio_bytes)
                logger.debug("Audio delta forwarded to callback")

    async def _handle_audio_done(self, data: Dict[str, Any]):
        """Handle audio done event."""
        logger.info("Audio response complete", size=len(self._response_audio))
        self._response_audio = bytearray()

    async def _handle_audio_transcript_delta(self, data: Dict[str, Any]):
        """Handle audio transcript delta."""
        delta = data.get("delta", "")
        if self.on_transcription:
            await self.on_transcription(delta, "assistant")

    async def _handle_response_done(self, data: Dict[str, Any]):
        """Handle response done event."""
        response = data.get("response", {})
        status = response.get("status")
        logger.info("Response complete", status=status)

        # FEATURE: Trigger chat history save callback
        if self.on_response_done:
            await self.on_response_done(data)

    @staticmethod
    async def _handle_speech_started(data: Dict[str, Any]):
        """Handle speech started event."""
        logger.info("User speech started")

    @staticmethod
    async def _handle_speech_stopped(data: Dict[str, Any]):
        """Handle speech stopped event."""
        logger.info("User speech stopped")

    async def _handle_buffer_committed(self, data: Dict[str, Any]):
        """Handle buffer committed event (triggered by VAD or manual commit)."""
        logger.info("Audio buffer committed by OpenAI")
        if self.on_buffer_committed:
            await self.on_buffer_committed(data)