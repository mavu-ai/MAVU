"""WebSocket handler for real-time audio streaming with RAG."""
import json
import asyncio
import base64
from typing import Any, Dict, Optional
from datetime import datetime
from uuid import uuid4
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
import structlog

from realtime.openai_client import OpenAIRealtimeClient, RealtimeSession
from rag.pipeline import rag_pipeline, RAGContextManager
from utils.redis_client import redis_client
from utils.embeddings import QuotaExceededError
from config import settings, SKINS
from models.chat import Chat
from models.user import User
from services.user_info_extraction_service import UserInfoExtractionService
from services.user_profile_updater import UserProfileUpdater
from utils.text_filter import clean_chat_message, is_meaningful_text

logger = structlog.get_logger()


class RealtimeStreamHandler:
    """Handle real-time audio streaming with RAG integration."""

    def __init__(self, websocket: WebSocket, user_id: str, db: Optional[Session] = None):
        self.websocket = websocket
        self.user_id = user_id
        self.db = db
        self.session_id = str(uuid4())
        self.openai_client = None
        self.rag_manager = RAGContextManager(rag_pipeline)
        self.is_active = False
        self.ws_connected = False  # Track WebSocket connection state
        self.ws_ready = False  # Track if WebSocket handshake is fully complete

        # FEATURE: Chat history tracking
        self.current_user_message = ""
        self.current_assistant_response = ""
        self.db_user_id = None  # Will be set when we save to database

        # Message queue for messages sent before WebSocket is fully ready
        self.message_queue = []
        self.max_queue_size = 10  # Prevent memory issues

        # Audio buffer tracking
        self.audio_buffer_size = 0  # Track accumulated audio in bytes

        # User preferences
        self.user_voice = "shimmer"  # Default voice, will be updated based on skin_id

        # Track if welcome message was already triggered to prevent duplicates
        self.welcome_triggered = False
        self.audio_buffer_duration_ms = 0.0  # Track duration in milliseconds
        self.audio_chunk_count = 0  # Count chunks received
        self.last_audio_chunk_time = None
        self.min_buffer_duration_ms = 100  # Minimum 100ms required by OpenAI
        self.sample_rate = 24000  # 24kHz
        self.bytes_per_ms = (self.sample_rate * 2) / 1000  # PCM16 = 2 bytes per sample

        # Network latency tracking for dynamic grace period
        self.chunk_receive_times = []  # Track last 10 chunk intervals
        self.max_latency_samples = 10

        # Performance metrics
        self.metrics: dict[str, float] = {
            "total_audio_chunks": 0,
            "total_text_chunks": 0,
            "rag_queries": 0,
            "avg_response_time": 0,
            "audio_commits": 0,
            "rejected_commits": 0
        }

    async def start(self):
        """Start the real-time streaming session."""
        try:
            # Accept WebSocket connection
            await self.websocket.accept()
            self.ws_connected = True
            logger.info("WebSocket accepted", session_id=self.session_id, user_id=self.user_id)

            # CRITICAL FIX: Wait for WebSocket handshake to fully complete
            # Poll the client_state until it's CONNECTED to avoid "need to call accept" errors
            max_wait_attempts = 20  # 20 attempts * 50ms = 1 second max wait
            wait_attempt = 0

            while wait_attempt < max_wait_attempts:
                try:
                    client_state = self.websocket.client_state.name
                    if client_state == "CONNECTED":
                        logger.info("WebSocket client state is CONNECTED", attempts=wait_attempt + 1)
                        break
                    logger.debug("Waiting for CONNECTED state", current_state=client_state, attempt=wait_attempt + 1)
                    await asyncio.sleep(0.05)  # 50ms increments
                    wait_attempt += 1
                except Exception as e:
                    logger.error("Error checking WebSocket state", error=str(e))
                    break

            # Mark as ready and flush any queued messages
            self.ws_ready = True
            try:
                await self._flush_message_queue()
            except Exception as flush_error:
                logger.error("Failed to flush message queue", error=str(flush_error))
                # Continue anyway - connection is still valid

            # Send connecting message now that we're truly ready
            await self._send_to_client({
                "type": "session.connecting",
                "session_id": self.session_id,
                "status": "initializing"
            })

            # Initialize OpenAI client with callbacks
            self.openai_client = OpenAIRealtimeClient(
                on_transcription=self._handle_transcription,
                on_text_delta=self._handle_text_delta,
                on_audio_delta=self._handle_audio_delta,
                on_error=self._handle_error,
                on_buffer_committed=self._handle_buffer_committed,
                on_response_done=self._handle_response_complete
            )

            # Get initial system instructions with user context
            try:
                system_instructions = await asyncio.wait_for(
                    self._prepare_system_instructions(),
                    timeout=10.0  # 10 second timeout for RAG context
                )
            except asyncio.TimeoutError:
                logger.warning("RAG context timeout, using default instructions")
                system_instructions = """You are a helpful AI assistant."""

            # Load user's voice preference from skin_id
            await self._load_user_voice()

            logger.info(
                "Configuring OpenAI session with user preferences",
                user_id=self.user_id,
                voice=self.user_voice,
                model=settings.openai_model
            )

            # Configure session with optimized Russian language support
            session_config = RealtimeSession(
                model=settings.openai_model,
                instructions=system_instructions,
                voice=self.user_voice,  # Voice based on user's selected skin
                input_audio_format="pcm16",
                output_audio_format="pcm16",
                modalities=["text", "audio"],
                input_audio_transcription={
                    "model": "whisper-1",
                    "language": "ru"  # Explicit Russian for faster recognition
                },
                turn_detection={
                    "type": "server_vad",
                    "threshold": 0.85,  # OPTIMIZED: Very high threshold to reduce sensitivity and prevent false detections (was 0.75)
                    "prefix_padding_ms": 300,  # Padding for speech start
                    "silence_duration_ms": 700,  # OPTIMIZED: Longer silence to avoid cutting off speech and reduce false triggers (was 500)
                },
                temperature=0.8  # Natural, conversational responses
            )

            # Connect to OpenAI with timeout and error handling
            try:
                logger.info("Connecting to OpenAI Realtime API...")
                await asyncio.wait_for(
                    self.openai_client.connect(session_config),
                    timeout=15.0  # 15 second timeout for OpenAI connection
                )
                logger.info("OpenAI connection established successfully")
            except asyncio.TimeoutError:
                error_msg = "OpenAI connection timeout. Please check your API key and network connection."
                logger.error("OpenAI connection timeout")
                await self._send_error_to_client(error_msg)
                raise Exception(error_msg)
            except Exception as e:
                error_msg = f"Failed to connect to OpenAI: {str(e)}"
                logger.error("OpenAI connection failed", error=str(e))
                await self._send_error_to_client(error_msg)
                raise

            # Mark session as active
            self.is_active = True

            # Send ready message after successful OpenAI connection
            await self._send_to_client({
                "type": "session.ready",
                "session_id": self.session_id,
                "model": settings.openai_model,
                "voice": self.user_voice,  # Include voice so frontend can verify
                "status": "ready"
            })

            logger.info("Session fully initialized and ready", session_id=self.session_id)

            # Trigger initial welcome message for guest users
            if self.db:
                try:
                    # Query user from database with detailed logging
                    logger.debug("Querying user for welcome message check", user_id=self.user_id)
                    user = self.db.query(User).filter(User.id == int(self.user_id)).first()

                    if not user:
                        logger.warning("User not found in database for welcome message",
                                      user_id=self.user_id)
                    else:
                        # Log user's current state
                        logger.info(
                            "User profile checked for welcome message",
                            user_id=self.user_id,
                            name=user.name,
                            age=user.age,
                            gender=user.gender,
                            is_guest=user.is_guest,
                            language=user.language
                        )

                        # Check if user is a guest (missing profile information)
                        # CRITICAL: Only trigger once to prevent duplicate audio
                        if user.is_guest and not self.welcome_triggered:
                            logger.info(
                                "Guest user detected - preparing welcome message",
                                user_id=self.user_id,
                                user_language=user.language,
                                welcome_already_triggered=self.welcome_triggered
                            )

                            # Mark as triggered immediately to prevent duplicates
                            self.welcome_triggered = True

                            # Verify that onboarding prompt was added to system instructions
                            if "зовут" in self.openai_client.session.instructions or \
                               "name is" in self.openai_client.session.instructions.lower():
                                logger.info("Onboarding prompt confirmed in system instructions")
                            else:
                                logger.warning(
                                    "Onboarding prompt NOT found in system instructions - "
                                    "welcome message may not work correctly"
                                )

                            # Give OpenAI time to initialize and settle
                            # This ensures the WebSocket is ready and session is configured
                            # 1 second delay as requested for faster response
                            await asyncio.sleep(1.0)

                            # Verify OpenAI is still connected before triggering
                            if not self.openai_client or not self.openai_client.is_connected:
                                logger.error(
                                    "Cannot trigger welcome message: OpenAI disconnected",
                                    user_id=self.user_id
                                )
                            else:
                                # Send a preparation message to the client to get audio ready
                                await self._send_to_client({
                                    "type": "audio.preparing",
                                    "message": "Preparing welcome message"
                                })

                                # No additional delay - total is now 1 second
                                logger.debug("Triggering welcome message after 1s delay")

                                # Trigger OpenAI to generate the welcome greeting
                                # The system instructions already contain the onboarding prompt
                                # so OpenAI will respond with the appropriate greeting
                                logger.info(
                                    "WELCOME_TRIGGER: Triggering OpenAI to speak welcome message",
                                    user_id=self.user_id,
                                    session_id=self.session_id,
                                    modalities=["text", "audio"],
                                    timestamp=datetime.now().isoformat()
                                )

                                await self.openai_client.create_response(
                                    modalities=["text", "audio"]
                                )

                                logger.info(
                                    "WELCOME_TRIGGER: Welcome response triggered successfully for guest user",
                                    user_id=self.user_id,
                                    session_id=self.session_id,
                                    timestamp=datetime.now().isoformat()
                                )
                        elif user.is_guest and self.welcome_triggered:
                            logger.warning(
                                "Guest user but welcome already triggered - skipping duplicate",
                                user_id=self.user_id,
                                welcome_already_triggered=self.welcome_triggered
                            )
                        else:
                            logger.info(
                                "User is not a guest - skipping welcome message",
                                user_id=self.user_id,
                                has_name=bool(user.name),
                                has_age=bool(user.age),
                                has_gender=bool(user.gender),
                                welcome_already_triggered=self.welcome_triggered
                            )

                except ValueError as e:
                    logger.error(
                        "Invalid user_id format for welcome message",
                        user_id=self.user_id,
                        error=str(e),
                        error_type="ValueError"
                    )
                except Exception as e:
                    logger.error(
                        "Failed to trigger welcome message",
                        user_id=self.user_id,
                        error=str(e),
                        error_type=type(e).__name__,
                        has_db=bool(self.db),
                        has_openai_client=bool(self.openai_client)
                    )
                    # Don't fail the session - user can still speak first

            # Handle messages
            await self._handle_messages()

        except WebSocketDisconnect:
            logger.info("WebSocket disconnected", session_id=self.session_id)
            self.ws_connected = False
        except RuntimeError as e:
            # Handle WebSocket connection errors gracefully
            if "not connected" in str(e).lower() or "accept" in str(e).lower():
                logger.info("WebSocket connection closed (expected)", error=str(e), session_id=self.session_id)
            else:
                logger.error("Runtime error in session", error=str(e), session_id=self.session_id)
            self.ws_connected = False
        except Exception as e:
            logger.error("WebSocket error", error=str(e), session_id=self.session_id)
            # Only try to send error if WebSocket is still connected
            if self.ws_connected:
                try:
                    await self._send_error_to_client(str(e))
                except Exception as send_error:
                    logger.warning("Could not send error to client (connection closed)", error=str(send_error))
            self.ws_connected = False
        finally:
            await self.cleanup()

    async def _handle_messages(self):
        """Handle incoming WebSocket messages."""
        try:
            while self.is_active:
                # Receive message from client
                message = await self.websocket.receive_text()
                data = json.loads(message)

                message_type = data.get("type")
                logger.debug("Received message", type=message_type)

                if message_type == "audio.append":
                    await self._handle_audio_input(data)
                elif message_type == "audio.commit":
                    await self._handle_audio_commit()
                elif message_type == "text.input":
                    await self._handle_text_input(data)
                elif message_type == "context.refresh":
                    await self._refresh_context(data)
                elif message_type == "voice.change":
                    await self._handle_voice_change(data)
                elif message_type == "session.end":
                    break
                else:
                    logger.warning("Unknown message type", type=message_type)

        except WebSocketDisconnect:
            logger.info("Client disconnected", session_id=self.session_id)
        except RuntimeError as e:
            # Handle WebSocket connection errors gracefully - these are expected when client disconnects
            if "not connected" in str(e).lower() or "accept" in str(e).lower():
                logger.info("WebSocket closed during message handling (expected)", error=str(e))
                self.ws_connected = False
                self.ws_ready = False
                # Don't re-raise - this is expected behavior
            else:
                logger.error("Runtime error in message handling", error=str(e))
                raise
        except Exception as e:
            logger.error("Message handling error", error=str(e))
            raise

    async def _handle_audio_input(self, data: Dict[str, Any]):
        """Handle incoming audio data."""
        try:
            # Check OpenAI connection before processing
            if not self.openai_client or not self.openai_client.is_connected:
                logger.warning("Cannot process audio: OpenAI not connected")
                await self._send_error_to_client("Session not ready. Please wait for connection.")
                return

            audio_base64 = data.get("audio")
            if not audio_base64:
                return

            # Decode base64 audio
            audio_bytes = base64.b64decode(audio_base64)

            # Track buffer size and duration
            chunk_size = len(audio_bytes)
            # PCM16: 2 bytes per sample, 24000 Hz
            chunk_duration_ms = (chunk_size / 2) / self.sample_rate * 1000

            current_time = asyncio.get_event_loop().time()

            # Track chunk interval for latency estimation
            if self.last_audio_chunk_time is not None:
                interval = current_time - self.last_audio_chunk_time
                self.chunk_receive_times.append(interval)
                # Keep only last N samples
                if len(self.chunk_receive_times) > self.max_latency_samples:
                    self.chunk_receive_times.pop(0)

            self.audio_buffer_size += chunk_size
            self.audio_buffer_duration_ms += chunk_duration_ms
            self.audio_chunk_count += 1
            self.last_audio_chunk_time = current_time

            logger.info(
                "Audio chunk received",
                chunk_size=chunk_size,
                chunk_duration_ms=f"{chunk_duration_ms:.1f}",
                total_buffer_ms=f"{self.audio_buffer_duration_ms:.1f}",
                chunk_count=self.audio_chunk_count
            )

            # Send to OpenAI
            await self.openai_client.send_audio(audio_bytes)

            self.metrics["total_audio_chunks"] += 1

            # Send acknowledgment
            await self._send_to_client({
                "type": "audio.received",
                "chunk_id": data.get("chunk_id")
            })

        except Exception as e:
            logger.error("Failed to handle audio input", error=str(e))

    async def _handle_audio_commit(self):
        """Commit audio buffer for processing with validation."""
        try:
            # Check OpenAI connection before processing
            if not self.openai_client or not self.openai_client.is_connected:
                logger.warning("Cannot commit audio: OpenAI not connected")
                await self._send_error_to_client("Session not ready. Please wait for connection.")
                return

            logger.info(
                "Audio commit requested",
                buffer_duration_ms=f"{self.audio_buffer_duration_ms:.1f}",
                chunk_count=self.audio_chunk_count,
                buffer_size_bytes=self.audio_buffer_size
            )

            # EARLY VALIDATION: Check if we have ANY audio at all before grace period
            if self.audio_chunk_count == 0 and self.audio_buffer_duration_ms == 0:
                logger.warning(
                    "EMPTY BUFFER: No audio received - rejecting commit immediately",
                    buffer_ms=f"{self.audio_buffer_duration_ms:.1f}",
                    chunk_count=self.audio_chunk_count,
                    message="Instant microphone click detected - no audio chunks received"
                )

                self.metrics["rejected_commits"] += 1

                # Send friendly notification to client (not an error)
                await self._send_to_client({
                    "type": "response.done",
                    "status": "no_audio",
                    "message": "No audio captured"
                })

                return

            # IMPROVED: Dynamic grace period based on network latency
            # Calculate average chunk interval to estimate network latency
            if self.chunk_receive_times:
                avg_interval = sum(self.chunk_receive_times) / len(self.chunk_receive_times)
                max_interval = max(self.chunk_receive_times)
                # Use 2x average or max observed interval, whichever is larger, with min 150ms and max 500ms
                grace_period_s = max(0.15, min(0.5, max(avg_interval * 2, max_interval)))
            else:
                # Default to 200ms if we have no latency data
                grace_period_s = 0.2

            logger.info(
                "Waiting for in-flight audio chunks (dynamic grace period)",
                grace_period_ms=f"{grace_period_s * 1000:.0f}",
                avg_interval_ms=f"{sum(self.chunk_receive_times) / len(self.chunk_receive_times) * 1000:.0f}" if self.chunk_receive_times else "N/A",
                max_interval_ms=f"{max(self.chunk_receive_times) * 1000:.0f}" if self.chunk_receive_times else "N/A"
            )
            await asyncio.sleep(grace_period_s)

            # Log buffer state after grace period
            logger.info(
                "Buffer state after grace period",
                buffer_duration_ms=f"{self.audio_buffer_duration_ms:.1f}",
                chunk_count=self.audio_chunk_count,
                buffer_size_bytes=self.audio_buffer_size
            )

            # VALIDATE: Check if buffer has enough audio (minimum 100ms required by OpenAI)
            if self.audio_buffer_duration_ms < self.min_buffer_duration_ms:
                logger.warning(
                    "INSUFFICIENT BUFFER: Buffer too small after grace period - silently rejecting",
                    buffer_ms=f"{self.audio_buffer_duration_ms:.1f}",
                    required_ms=self.min_buffer_duration_ms,
                    chunk_count=self.audio_chunk_count,
                    message="User likely clicked microphone too quickly or spoke very briefly"
                )

                self.metrics["rejected_commits"] += 1

                # Reset buffer state
                self.audio_buffer_size = 0
                self.audio_buffer_duration_ms = 0.0
                self.audio_chunk_count = 0

                # Send completion notification to client (not an error - just insufficient audio)
                await self._send_to_client({
                    "type": "response.done",
                    "status": "insufficient_audio",
                    "message": "Recording too short"
                })

                return

            # Buffer validation passed - commit to OpenAI
            logger.info(
                "BUFFER VALID: Committing to OpenAI",
                buffer_ms=f"{self.audio_buffer_duration_ms:.1f}",
                chunk_count=self.audio_chunk_count,
                buffer_size_bytes=self.audio_buffer_size
            )

            # Commit to OpenAI with error handling
            try:
                await self.openai_client.commit_audio()
                self.metrics["audio_commits"] += 1
                logger.info("Audio committed to OpenAI successfully", buffer_ms=f"{self.audio_buffer_duration_ms:.1f}")
            except Exception as commit_error:
                # Check if it's the empty buffer error from OpenAI (should not happen with our validation)
                error_str = str(commit_error).lower()
                if "buffer" in error_str and ("empty" in error_str or "too small" in error_str or "0.00ms" in error_str):
                    # CRITICAL FIX: This shouldn't happen with our validation, but suppress if it does
                    logger.warning(
                        "OpenAI rejected buffer despite validation - edge case detected",
                        error=str(commit_error),
                        buffer_ms=f"{self.audio_buffer_duration_ms:.1f}",
                        chunk_count=self.audio_chunk_count,
                        message="Suppressed error - validation gap detected"
                    )
                    self.metrics["rejected_commits"] += 1

                    # Send completion notification
                    await self._send_to_client({
                        "type": "response.done",
                        "status": "openai_rejected",
                        "message": "Audio buffer rejected by OpenAI"
                    })
                else:
                    # Other errors should be reported
                    logger.error("Failed to commit audio to OpenAI", error=str(commit_error))
                    await self._send_error_to_client("Error processing audio. Please try again.")

                # Reset buffer regardless
                self.audio_buffer_size = 0
                self.audio_buffer_duration_ms = 0.0
                self.audio_chunk_count = 0
                return

            # Reset buffer tracking after successful commit
            self.audio_buffer_size = 0
            self.audio_buffer_duration_ms = 0.0
            self.audio_chunk_count = 0

        except Exception as e:
            logger.error("Failed to commit audio", error=str(e), error_type=type(e).__name__)
            # Reset on error too
            self.audio_buffer_size = 0
            self.audio_buffer_duration_ms = 0.0
            self.audio_chunk_count = 0
            # Don't send error to user for expected issues
            if "buffer" not in str(e).lower():
                await self._send_error_to_client("Error processing audio. Please try again.")

    async def _handle_text_input(self, data: Dict[str, Any]):
        """Handle text input with RAG."""
        try:
            # Check OpenAI connection before processing
            if not self.openai_client or not self.openai_client.is_connected:
                logger.warning("Cannot process text: OpenAI not connected")
                await self._send_error_to_client("Session not ready. Please wait for connection.")
                return

            text = data.get("text", "")
            if not text:
                return

            start_time = asyncio.get_event_loop().time()

            # Prepare augmented instructions with RAG context
            augmented_instructions = await self.rag_manager.prepare_context(
                query=text,
                owner_id=self.user_id,
                system_instructions=self.openai_client.session.instructions
            )

            # Update session with new instructions (preserving voice setting)
            logger.info("Updating session with RAG context", voice=self.user_voice)
            await self.openai_client._send_event({
                "type": "session.update",
                "session": {
                    "instructions": augmented_instructions,
                    "voice": self.user_voice  # Preserve user's selected voice
                }
            })

            # Send text to OpenAI
            await self.openai_client.send_text(text)

            # Send retrieved context to client
            context = self.rag_manager.get_current_context()
            if context:
                await self._send_to_client({
                    "type": "context.retrieved",
                    "user_context": context.get("user_context", []),
                    "app_context": context.get("app_context", [])
                })

            # Update metrics
            self.metrics["rag_queries"] += 1
            response_time = asyncio.get_event_loop().time() - start_time
            self.metrics["avg_response_time"] = (
                (self.metrics["avg_response_time"] * (self.metrics["rag_queries"] - 1) + response_time)
                / self.metrics["rag_queries"]
            )

            logger.info("Text input processed with RAG", response_time=response_time)

        except Exception as e:
            logger.error("Failed to handle text input", error=str(e))

    async def _refresh_context(self, data: Dict[str, Any]):
        """Refresh RAG context on demand."""
        try:
            query = data.get("query", "")
            if query:
                context = await rag_pipeline.retrieve_context(
                    query=query,
                    owner_id=self.user_id
                )
                await self._send_to_client({
                    "type": "context.refreshed",
                    "context": context
                })
        except Exception as e:
            logger.error("Failed to refresh context", error=str(e))

    async def _handle_voice_change(self, data: Dict[str, Any]):
        """Change the assistant voice during active session."""
        try:
            new_voice = data.get("voice")
            skin_id = data.get("skin_id")

            if not new_voice and not skin_id:
                logger.warning("Voice change requested without voice or skin_id")
                await self._send_error_to_client("Please provide either 'voice' or 'skin_id'")
                return

            # If skin_id provided, get voice from SKINS config
            if skin_id:
                from config import SKINS
                skin_config = SKINS.get(skin_id)
                if skin_config and "voice" in skin_config:
                    new_voice = skin_config["voice"]
                    logger.info(
                        "Voice from skin selected",
                        skin_id=skin_id,
                        skin_name=skin_config["name"],
                        new_voice=new_voice
                    )
                else:
                    logger.warning("Invalid skin_id", skin_id=skin_id)
                    await self._send_error_to_client(f"Invalid skin_id: {skin_id}")
                    return

            # List of valid OpenAI voices
            valid_voices = ["alloy", "ash", "ballad", "coral", "echo", "sage", "shimmer", "verse", "marin", "cedar"]

            if new_voice not in valid_voices:
                logger.warning("Invalid voice requested", voice=new_voice)
                await self._send_error_to_client(f"Invalid voice: {new_voice}. Valid options: {', '.join(valid_voices)}")
                return

            # Check OpenAI connection
            if not self.openai_client or not self.openai_client.is_connected:
                logger.warning("Cannot change voice: OpenAI not connected")
                await self._send_error_to_client("Session not ready. Please wait for connection.")
                return

            # Store old voice for logging
            old_voice = self.user_voice

            # Update the voice
            self.user_voice = new_voice

            # Update the OpenAI session with the new voice
            logger.info(
                "Updating voice in active session",
                user_id=self.user_id,
                old_voice=old_voice,
                new_voice=new_voice,
                session_id=self.session_id
            )

            await self.openai_client._send_event({
                "type": "session.update",
                "session": {
                    "voice": new_voice
                }
            })

            # Update user's skin preference in database if skin_id was provided
            if skin_id and self.db:
                try:
                    from models.user import User
                    user = self.db.query(User).filter(User.id == int(self.user_id)).first()
                    if user:
                        user.skin_id = skin_id
                        self.db.commit()
                        logger.info(
                            "User skin_id updated in database",
                            user_id=self.user_id,
                            skin_id=skin_id
                        )
                except Exception as db_error:
                    logger.error("Failed to update user skin_id", error=str(db_error))
                    # Don't fail the voice change if database update fails
                    if self.db:
                        self.db.rollback()

            # Send confirmation to client
            await self._send_to_client({
                "type": "voice.changed",
                "old_voice": old_voice,
                "new_voice": new_voice,
                "message": f"Voice changed from {old_voice} to {new_voice}"
            })

            logger.info(
                "Voice successfully changed",
                user_id=self.user_id,
                from_voice=old_voice,
                to_voice=new_voice
            )

        except Exception as e:
            logger.error("Failed to change voice", error=str(e), error_type=type(e).__name__)
            await self._send_error_to_client("Failed to change voice. Please try again.")

    async def _load_user_voice(self) -> None:
        """Load user's voice preference based on their selected skin_id."""
        if not self.db:
            logger.info("No database connection, using default voice", voice=self.user_voice)
            return

        try:
            from models.user import User
            user = self.db.query(User).filter(User.id == int(self.user_id)).first()

            logger.info(
                "Loading voice preference",
                user_id=self.user_id,
                user_found=user is not None,
                skin_id=user.skin_id if user else None,
                default_voice=self.user_voice
            )

            if user and user.skin_id:
                skin_config = SKINS.get(user.skin_id)
                logger.info(
                    "Skin lookup result",
                    skin_id=user.skin_id,
                    skin_config_found=skin_config is not None,
                    available_skins=list(SKINS.keys())
                )

                if skin_config and "voice" in skin_config:
                    self.user_voice = skin_config["voice"]
                    logger.info(
                        "✓ Voice loaded successfully from user preferences",
                        user_id=self.user_id,
                        skin_id=user.skin_id,
                        skin_name=skin_config["name"],
                        voice=self.user_voice
                    )
                else:
                    logger.warning(
                        "Invalid skin_id or missing voice config, using default",
                        skin_id=user.skin_id,
                        voice=self.user_voice,
                        skin_config=skin_config
                    )
            else:
                logger.info("No user or skin_id found, using default voice",
                          user_found=user is not None,
                          skin_id=user.skin_id if user else None,
                          voice=self.user_voice)
        except Exception as e:
            logger.error("Failed to load user voice, using default",
                        error=str(e),
                        error_type=type(e).__name__,
                        voice=self.user_voice)

    async def _prepare_system_instructions(self) -> str:
        """Prepare initial system instructions with user context and chat history."""
        # Get user profile from database
        user = None
        user_name = None
        user_age = None
        user_gender = None

        if self.db:
            try:
                from models.user import User
                user = self.db.query(User).filter(User.id == int(self.user_id)).first()
                if user:
                    user_name = user.name
                    user_age = user.age
                    user_gender = user.gender
                    logger.info(
                        "User profile loaded",
                        name=user_name,
                        age=user_age,
                        gender=user_gender
                    )
            except Exception as e:
                logger.warning("Failed to load user profile", error=str(e))

        base_instructions = """You are MAVU, a friendly AI companion for children and young adults.
You speak warmly, naturally, and adapt to the user's age and interests.

IMPORTANT LANGUAGE GUIDELINES:
- When the user speaks Russian, respond in Russian with natural, fluent speech.
- When the user speaks English, respond in English.
- Match the user's language preference in all responses.
- Speak naturally and clearly with appropriate intonation.
- Keep responses concise for voice interaction (2-3 sentences when possible).
- Be friendly and conversational."""

        # Add onboarding section if user profile is incomplete
        if not user_name or not user_age:
            # Determine user's language preference
            user_language = "ru"  # Default to Russian
            if user:
                user_language = user.language or "ru"
                logger.info(
                    "User profile incomplete - adding onboarding prompts",
                    has_name=bool(user_name),
                    has_age=bool(user_age),
                    user_language=user_language
                )
            else:
                logger.info(
                    "User profile incomplete - adding onboarding prompts (no user object, defaulting to Russian)",
                    has_name=bool(user_name),
                    has_age=bool(user_age)
                )

            onboarding_section = UserInfoExtractionService.build_onboarding_prompt_section(
                user_name=user_name,
                user_age=user_age,
                user_gender=user_gender,
                language=user_language
            )

            if onboarding_section:
                base_instructions += "\n\n" + onboarding_section
                logger.debug(
                    "Onboarding section added to system instructions",
                    language=user_language,
                    section_length=len(onboarding_section)
                )

        # Get recent chat history from Redis (last 10 conversations)
        try:
            recent_chats = await redis_client.get_recent_voice_chats(self.user_id, limit=10)
            if recent_chats:
                # Format chat history
                chat_history = "\n".join([
                    f"{chat['role'].title()}: {chat['message']}"
                    for chat in recent_chats[-6:]  # Last 6 messages (3 exchanges)
                ])
                base_instructions += f"\n\nRecent Conversation History:\n{chat_history}"
                logger.info("Added chat history to instructions", message_count=len(recent_chats))
        except Exception as e:
            logger.warning("Failed to load chat history from Redis", error=str(e))
            # Continue without chat history - don't fail

        # Get some initial context about the user from RAG
        try:
            initial_context = await rag_pipeline.retrieve_context(
                query="user preferences and history",
                owner_id=self.user_id,
                top_k_user=3,
                top_k_app=2
            )

            # Check for quota exceeded
            if initial_context.get("quota_exceeded"):
                logger.warning("RAG quota exceeded - continuing without personalized context")
            elif initial_context.get("user_context"):
                user_info = "\n".join([
                    f"- {item['text']}"
                    for item in initial_context["user_context"][:2]
                ])
                base_instructions += f"\n\nUser Background:\n{user_info}"
        except QuotaExceededError:
            logger.warning("OpenAI quota exceeded during context retrieval - continuing without RAG")
        except Exception as e:
            logger.warning("Failed to retrieve initial context", error=str(e))
            # Continue without RAG context - don't fail

        return base_instructions

    # Callback handlers for OpenAI events
    async def _handle_transcription(self, text: str, role: str):
        """Handle transcription from OpenAI."""
        try:
            await self._send_to_client({
                "type": "transcription",
                "text": text,
                "role": role
            })

            # FEATURE: Track transcriptions for chat history
            if role == "user" and text:
                self.current_user_message = text

                # Prepare context in background
                asyncio.create_task(self._update_context_async(text))
            elif role == "assistant" and text:
                self.current_assistant_response += text

        except Exception as e:
            logger.error("Failed to handle transcription", error=str(e))

    async def _update_context_async(self, text: str):
        """Update context asynchronously based on transcription with error handling."""
        try:
            augmented_instructions = await self.rag_manager.prepare_context(
                query=text,
                owner_id=self.user_id,
                system_instructions=self.openai_client.session.instructions
            )

            # Update OpenAI session (preserving voice setting)
            await self.openai_client._send_event({
                "type": "session.update",
                "session": {
                    "instructions": augmented_instructions,
                    "voice": self.user_voice  # Preserve user's selected voice
                }
            })

            # Send context to client with detailed RAG results
            context = self.rag_manager.get_current_context()
            if context:
                # Check if quota was exceeded
                if context.get("quota_exceeded"):
                    logger.info("RAG quota exceeded - continuing without context")
                    # Don't send error to user - they don't need to know
                else:
                    # Log full RAG results for monitoring
                    logger.info(
                        "RAG context retrieved",
                        user_id=self.user_id,
                        user_context_count=len(context.get("user_context", [])),
                        app_context_count=len(context.get("app_context", [])),
                        query=text[:100]
                    )

                    # Send detailed context to client (send more than just 2 items)
                    await self._send_to_client({
                        "type": "context.updated",
                        "user_context": context.get("user_context", [])[:5],  # Send top 5 instead of 2
                        "app_context": context.get("app_context", [])[:5],     # Send top 5 instead of 2
                        "retrieval_method": context.get("retrieval_method", "hybrid"),
                        "query": text[:100]  # Include query for reference
                    })

                    # Log RAG sources for debugging
                    if context.get("user_context"):
                        logger.debug(
                            "User context sources",
                            sources=[ctx.get("text", "")[:100] for ctx in context.get("user_context", [])[:3]]
                        )
                    if context.get("app_context"):
                        logger.debug(
                            "App context sources",
                            sources=[ctx.get("text", "")[:100] for ctx in context.get("app_context", [])[:3]]
                        )

        except QuotaExceededError:
            logger.info("OpenAI quota exceeded during context update - continuing without RAG")
            # Graceful degradation - don't show error to user
        except Exception as e:
            logger.error("Failed to update context", error=str(e), error_type=type(e).__name__)
            # Don't send error to user - context update failure shouldn't disrupt chat

    async def _extract_and_update_user_info(self, user_message: str, assistant_response: str):
        """
        Extract and update user info with smart validation.

        Uses UserProfileUpdater for safe, validated updates.
        """
        try:
            if not self.db:
                return

            # Refresh the database session to get latest data
            self.db.expire_all()

            # Get current user from database
            user = self.db.query(User).filter(User.id == int(self.user_id)).first()
            if not user:
                logger.warning("User not found for info extraction", user_id=self.user_id)
                return

            # Use the smart updater
            result = await UserProfileUpdater.update_user_profile(
                user=user,
                user_message=user_message,
                assistant_response=assistant_response,
                db=self.db
            )

            # Handle update results
            if result['success'] and result['updated']:
                # Send notification to client
                await self._send_to_client({
                    "type": "profile.updated",
                    "name": user.name,
                    "age": user.age,
                    "gender": user.gender,
                    "updates": result['updates']
                })

                # Update system instructions if profile is now complete
                if user.name and user.age:
                    logger.info("User profile complete - updating system instructions")
                    new_instructions = await self._prepare_system_instructions()
                    await self.openai_client._send_event({
                        "type": "session.update",
                        "session": {
                            "instructions": new_instructions,
                            "voice": self.user_voice  # Preserve user's selected voice
                        }
                    })

        except Exception as e:
            logger.error("Failed to extract/update user info", error=str(e), error_type=type(e).__name__)
            if self.db:
                try:
                    self.db.rollback()
                except Exception:
                    pass

    async def _handle_text_delta(self, delta: str):
        """Handle text delta from OpenAI."""
        try:
            await self._send_to_client({
                "type": "text.delta",
                "delta": delta
            })
            self.metrics["total_text_chunks"] += 1
        except Exception as e:
            logger.error("Failed to handle text delta", error=str(e))

    async def _handle_audio_delta(self, audio_bytes: bytes):
        """Handle audio delta from OpenAI."""
        try:
            # Convert to base64 for WebSocket transmission
            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')

            # Generate unique chunk ID for tracking
            chunk_id = f"{self.session_id}_{datetime.now().timestamp()}_{len(audio_bytes)}"

            logger.info(
                "AUDIO_DELTA: Forwarding audio to client",
                session_id=self.session_id,
                user_id=self.user_id,
                chunk_id=chunk_id,
                bytes_count=len(audio_bytes),
                base64_length=len(audio_base64),
                timestamp=datetime.now().isoformat()
            )
            await self._send_to_client({
                "type": "audio.delta",
                "audio": audio_base64,
                "chunk_id": chunk_id  # Add chunk ID for duplicate detection
            })
        except Exception as e:
            logger.error("Failed to handle audio delta", error=str(e))

    async def _handle_error(self, error: Dict[str, Any]):
        """Handle errors from OpenAI."""
        # CRITICAL FIX: Filter out empty/insufficient buffer errors - these are expected
        # when users click microphone quickly or speak very briefly
        error_code = error.get("code", "")
        error_message = error.get("message", "")
        error_type = error.get("type", "")

        # Suppress expected buffer validation errors
        if error_code == "input_audio_buffer_commit_empty" or \
           "buffer too small" in error_message.lower() or \
           "0.00ms" in error_message:
            logger.info(
                "OpenAI buffer validation error (suppressed - expected behavior)",
                error_code=error_code,
                error_type=error_type,
                error_message=error_message
            )
            self.metrics["rejected_commits"] += 1

            # Send friendly completion message instead of error
            await self._send_to_client({
                "type": "response.done",
                "status": "insufficient_audio",
                "message": "Recording too short or empty"
            })
            return

        # All other errors should be logged and reported
        logger.error("OpenAI error", error=error)
        await self._send_error_to_client(str(error))

    async def _handle_buffer_committed(self, data: Dict[str, Any]):
        """Handle buffer committed event from OpenAI (VAD or manual)."""
        logger.info("Buffer committed notification received from OpenAI (VAD triggered)")
        # Reset buffer tracking since OpenAI has committed
        self.audio_buffer_size = 0
        self.audio_buffer_duration_ms = 0.0
        self.audio_chunk_count = 0

    async def _handle_response_complete(self, data: Dict[str, Any]):
        """Handle response completion - save chat history to Redis and database."""
        try:
            if not self.current_user_message:
                logger.debug("No user message to save")
                return

            # FEATURE: Extract user info BEFORE filtering (use original messages for better extraction)
            if self.db:
                try:
                    await self._extract_and_update_user_info(
                        self.current_user_message,
                        self.current_assistant_response
                    )
                except Exception as extract_err:
                    logger.error("Failed to extract user info", error=str(extract_err))
                    # Continue - extraction failure shouldn't break chat flow

            # CRITICAL FIX: Filter out emojis and meaningless content
            cleaned_user_message = clean_chat_message(self.current_user_message)
            cleaned_assistant_response = clean_chat_message(self.current_assistant_response)

            # Skip saving if the message is not meaningful (only emojis, noise, etc.)
            if not cleaned_user_message or not is_meaningful_text(self.current_user_message):
                logger.debug(
                    "Skipping non-meaningful message",
                    original=self.current_user_message[:50],
                    reason="only emojis or noise"
                )
                # Reset buffers
                self.current_user_message = ""
                self.current_assistant_response = ""
                return

            timestamp = datetime.now().isoformat()

            # FEATURE: Save to Redis for fast recent history retrieval
            try:
                # Save user message (use cleaned version)
                await redis_client.add_voice_chat(
                    user_id=self.user_id,
                    role="user",
                    message=cleaned_user_message,
                    timestamp=timestamp
                )
                # Save assistant response (use cleaned version if available)
                if cleaned_assistant_response:
                    await redis_client.add_voice_chat(
                        user_id=self.user_id,
                        role="assistant",
                        message=cleaned_assistant_response,
                        timestamp=timestamp
                    )
                logger.info(
                    "Voice chat saved to Redis",
                    user_id=self.user_id,
                    message_length=len(cleaned_user_message),
                    response_length=len(cleaned_assistant_response) if cleaned_assistant_response else 0
                )
            except Exception as redis_error:
                logger.warning("Failed to save chat to Redis", error=str(redis_error))
                # Continue - Redis failure shouldn't break the flow

            # FEATURE: Save voice chat to database for long-term storage
            if self.db:
                try:
                    # Get the database user ID if we don't have it yet
                    if not self.db_user_id:
                        user = self.db.query(User).filter(User.id == int(self.user_id)).first()
                        if user:
                            self.db_user_id = user.id
                        else:
                            logger.warning("User not found in database", user_id=self.user_id)
                            # Reset and return
                            self.current_user_message = ""
                            self.current_assistant_response = ""
                            return

                    # Build context with RAG context and chat history from Redis
                    context = {}

                    # Add RAG context if available with metadata
                    if hasattr(self.rag_manager, 'get_current_context'):
                        rag_context = self.rag_manager.get_current_context()
                        if rag_context:
                            context.update(rag_context)

                            # Add RAG summary for easy querying
                            context["rag_summary"] = {
                                "user_context_count": len(rag_context.get("user_context", [])),
                                "app_context_count": len(rag_context.get("app_context", [])),
                                "retrieval_method": rag_context.get("retrieval_method", "hybrid"),
                                "query": cleaned_user_message[:200],
                                "timestamp": datetime.now().isoformat()
                            }

                            # Log RAG usage for this chat
                            logger.info(
                                "RAG context saved to chat",
                                user_id=self.user_id,
                                user_contexts=len(rag_context.get("user_context", [])),
                                app_contexts=len(rag_context.get("app_context", []))
                            )

                    # Add chat history from Redis
                    try:
                        recent_chats = await redis_client.get_recent_voice_chats(self.user_id, limit=20)
                        if recent_chats:
                            context["chat_history"] = recent_chats
                            logger.debug("Added chat history to context", history_count=len(recent_chats))
                    except Exception as redis_err:
                        logger.warning("Failed to load chat history for context", error=str(redis_err))
                        # Continue without chat history

                    # Create chat record (use cleaned messages)
                    chat = Chat(
                        user_id=self.db_user_id,
                        message=cleaned_user_message,
                        response=cleaned_assistant_response or "(No response)",
                        processed=False,
                        context=context if context else None
                    )

                    self.db.add(chat)
                    self.db.commit()

                    logger.info(
                        "Voice chat saved to database",
                        user_id=self.user_id,
                        chat_id=chat.id
                    )
                except Exception as db_error:
                    logger.error("Failed to save chat to database", error=str(db_error), user_id=self.user_id)
                    if self.db:
                        self.db.rollback()
                    # Continue - DB failure shouldn't break the conversation
            else:
                logger.debug("No database session available, skipping database save")

            # Reset for next conversation
            self.current_user_message = ""
            self.current_assistant_response = ""

            # CRITICAL FIX: Send response.done to client to clear processing state
            await self._send_to_client({
                "type": "response.done",
                "status": "completed"
            })
            logger.info("Response done message sent to client")

        except Exception as e:
            logger.error("Failed to handle response complete", error=str(e), user_id=self.user_id)
            # Reset state to prevent issues with next conversation
            self.current_user_message = ""
            self.current_assistant_response = ""

            # CRITICAL FIX: Even on error, send completion to clear UI state
            try:
                await self._send_to_client({
                    "type": "response.done",
                    "status": "error"
                })
            except Exception as send_err:
                logger.error("Failed to send error response.done", error=str(send_err))

    async def _send_to_client(self, message: Dict[str, Any]):
        """Send message to WebSocket client with robust error handling and queueing."""
        if not self.ws_connected:
            logger.warning("Cannot send message: WebSocket not connected", message_type=message.get("type"))
            return

        # CRITICAL FIX: Queue messages if WebSocket handshake not complete yet
        if not self.ws_ready:
            if len(self.message_queue) < self.max_queue_size:
                self.message_queue.append(message)
                logger.debug(
                    "Message queued (WebSocket not ready)",
                    message_type=message.get("type"),
                    queue_size=len(self.message_queue)
                )
            else:
                logger.warning(
                    "Message queue full, dropping message",
                    message_type=message.get("type"),
                    queue_size=len(self.message_queue)
                )
            return

        try:
            # Check WebSocket client state before sending
            client_state = self.websocket.client_state.name
            application_state = self.websocket.application_state.name

            logger.debug(
                "WebSocket state check",
                client_state=client_state,
                application_state=application_state,
                message_type=message.get("type")
            )

            if client_state != "CONNECTED":
                logger.warning(
                    "WebSocket not in CONNECTED state",
                    client_state=client_state,
                    application_state=application_state,
                    message_type=message.get("type")
                )
                self.ws_connected = False
                self.ws_ready = False
                return

            await self.websocket.send_text(json.dumps(message))
            logger.debug("Message sent successfully", message_type=message.get("type"))

        except WebSocketDisconnect as e:
            logger.warning(
                "WebSocket disconnected during send",
                message_type=message.get("type"),
                code=getattr(e, 'code', 'unknown')
            )
            self.ws_connected = False
            self.ws_ready = False
        except RuntimeError as e:
            # Handle "WebSocket is not connected" errors
            if "not connected" in str(e).lower() or "accept" in str(e).lower():
                logger.warning(
                    "WebSocket connection lost (RuntimeError)",
                    error=str(e),
                    message_type=message.get("type")
                )
                self.ws_connected = False
                self.ws_ready = False
            else:
                logger.error(
                    "Runtime error sending to client",
                    error=str(e),
                    message_type=message.get("type"),
                    error_type=type(e).__name__
                )
                self.ws_connected = False
                self.ws_ready = False
        except Exception as e:
            logger.error(
                "Failed to send to client",
                error=str(e),
                message_type=message.get("type"),
                error_type=type(e).__name__
            )
            self.ws_connected = False
            self.ws_ready = False

    async def _flush_message_queue(self):
        """Flush any queued messages after WebSocket is ready."""
        if not self.message_queue:
            return

        logger.info("Flushing message queue", queue_size=len(self.message_queue))

        # Send all queued messages in order
        for message in self.message_queue:
            try:
                await self.websocket.send_text(json.dumps(message))
                logger.debug("Queued message sent", message_type=message.get("type"))
            except Exception as e:
                logger.error(
                    "Failed to send queued message",
                    message_type=message.get("type"),
                    error=str(e)
                )

        # Clear the queue
        self.message_queue.clear()
        logger.info("Message queue flushed successfully")

    async def _send_error_to_client(self, error_message: str):
        """Send error message to client."""
        await self._send_to_client({
            "type": "error",
            "message": error_message
        })

    async def cleanup(self):
        """Clean up resources."""
        try:
            self.is_active = False

            # Send metrics before closing (only if still connected)
            if self.ws_connected:
                await self._send_to_client({
                    "type": "session.metrics",
                    "metrics": self.metrics
                })

            # Close OpenAI connection and clear resources
            if self.openai_client:
                await self.openai_client.disconnect()
                self.openai_client = None

            # Clear all buffers and tracking
            self.audio_buffer_size = 0
            self.audio_buffer_duration_ms = 0.0
            self.audio_chunk_count = 0
            self.last_audio_chunk_time = None

            # Mark WebSocket as disconnected
            self.ws_connected = False

            logger.info("Session cleaned up completely", session_id=self.session_id, metrics=self.metrics)
        except Exception as e:
            logger.error("Cleanup error", error=str(e))
            # Ensure we mark as disconnected even on error
            self.ws_connected = False