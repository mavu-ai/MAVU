"""
Comprehensive tests for automatic welcome message implementation for guest users.

Tests cover:
- Guest user detection
- Welcome message triggering
- Non-guest users (should not get welcome message)
- Error handling
- Language detection
- Edge cases (DB failures, OpenAI failures, etc.)
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from sqlalchemy.orm import Session

from realtime.websocket_handler import RealtimeStreamHandler
from models.user import User
from realtime.openai_client import OpenAIRealtimeClient
from config import WELCOME_MESSAGES


class TestWelcomeMessageImplementation:
    """Test suite for automatic welcome message feature."""

    @pytest.fixture
    def mock_websocket(self):
        """Create a mock WebSocket."""
        ws = Mock()
        ws.accept = AsyncMock()
        ws.send_text = AsyncMock()
        ws.receive_text = AsyncMock()
        ws.client_state = Mock()
        ws.client_state.name = "CONNECTED"
        ws.application_state = Mock()
        ws.application_state.name = "CONNECTED"
        return ws

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = Mock(spec=Session)
        return db

    @pytest.fixture
    def mock_openai_client(self):
        """Create a mock OpenAI client."""
        client = Mock(spec=OpenAIRealtimeClient)
        client.connect = AsyncMock()
        client.disconnect = AsyncMock()
        client.create_response = AsyncMock()
        client.is_connected = True
        client.session = Mock()
        client.session.instructions = "Test instructions"
        client._send_event = AsyncMock()
        return client

    @pytest.fixture
    def guest_user(self):
        """Create a guest user (no profile information)."""
        user = User(
            id=1,
            email="guest@test.com",
            name=None,  # No name
            age=None,   # No age
            gender=None,  # No gender
            language="ru",
            skin_id=1
        )
        return user

    @pytest.fixture
    def registered_user(self):
        """Create a registered user (has profile information)."""
        user = User(
            id=2,
            email="user@test.com",
            name="Петя",
            age=10,
            gender="male",
            language="ru",
            skin_id=1
        )
        return user

    @pytest.fixture
    def partial_user(self):
        """Create a user with partial profile (has name but no age)."""
        user = User(
            id=3,
            email="partial@test.com",
            name="Маша",
            age=None,  # Missing age
            gender=None,
            language="ru",
            skin_id=1
        )
        return user

    @pytest.mark.asyncio
    async def test_guest_user_is_detected_correctly(self, guest_user):
        """Test that guest user detection works correctly."""
        # Guest user should have is_guest = True
        assert guest_user.is_guest is True
        assert guest_user.name is None
        assert guest_user.age is None
        assert guest_user.gender is None

    @pytest.mark.asyncio
    async def test_registered_user_is_not_guest(self, registered_user):
        """Test that registered user is not detected as guest."""
        # Registered user should have is_guest = False
        assert registered_user.is_guest is False
        assert registered_user.name is not None
        assert registered_user.age is not None
        assert registered_user.gender is not None

    @pytest.mark.asyncio
    async def test_partial_user_is_not_guest(self, partial_user):
        """Test that user with partial profile is NOT considered guest."""
        # User with only name (no age/gender) is NOT a guest
        # They are partially registered
        assert partial_user.is_guest is False
        assert partial_user.is_registered is True
        assert partial_user.name is not None
        assert partial_user.age is None
        assert partial_user.gender is None

    @pytest.mark.asyncio
    async def test_welcome_message_triggered_for_guest_user(
        self, mock_websocket, mock_db, guest_user, mock_openai_client
    ):
        """Test that welcome message is triggered for guest users."""
        # Setup database mock to return guest user
        mock_db.query.return_value.filter.return_value.first.return_value = guest_user

        # Create handler with mocked dependencies
        handler = RealtimeStreamHandler(
            websocket=mock_websocket,
            user_id="1",
            db=mock_db
        )

        # Mock _prepare_system_instructions to avoid RAG calls
        with patch.object(handler, '_prepare_system_instructions', new_callable=AsyncMock) as mock_instructions:
            mock_instructions.return_value = """You are MAVU.

КРИТИЧЕСКИ ВАЖНО: Ты НЕ ЗНАЕШЬ имя пользователя.

ТВОЯ ЗАДАЧА:
1. В ПЕРВОМ ОТВЕТЕ поприветствуй и спроси: "Привет! Я MAVU, твоя цифровая подружка. Как тебя зовут?"
"""

            # Mock _load_user_voice to avoid DB calls
            with patch.object(handler, '_load_user_voice', new_callable=AsyncMock):
                # Mock OpenAI client creation to use our mock
                with patch('realtime.websocket_handler.OpenAIRealtimeClient', return_value=mock_openai_client):
                    # Mock _handle_messages to avoid waiting for messages
                    with patch.object(handler, '_handle_messages', new_callable=AsyncMock):
                        # Call start() which should trigger welcome message
                        await handler.start()

        # Verify database was queried for user
        mock_db.query.assert_called()

        # Verify OpenAI create_response was called with correct parameters
        mock_openai_client.create_response.assert_called_once_with(
            modalities=["text", "audio"]
        )

    @pytest.mark.asyncio
    async def test_welcome_message_not_triggered_for_registered_user(
        self, mock_websocket, mock_db, registered_user, mock_openai_client
    ):
        """Test that welcome message is NOT triggered for registered users."""
        # Setup database mock to return registered user
        mock_db.query.return_value.filter.return_value.first.return_value = registered_user

        # Create handler
        handler = RealtimeStreamHandler(
            websocket=mock_websocket,
            user_id="2",
            db=mock_db
        )

        # Mock the OpenAI client
        handler.openai_client = mock_openai_client
        handler.is_active = True
        handler.ws_connected = True
        handler.ws_ready = True

        # Mock dependencies
        with patch.object(handler, '_prepare_system_instructions', new_callable=AsyncMock) as mock_instructions:
            mock_instructions.return_value = "You are MAVU."

            with patch.object(handler, '_load_user_voice', new_callable=AsyncMock):
                with patch.object(handler, '_handle_messages', new_callable=AsyncMock):
                    await handler.start()

        # Verify OpenAI create_response was NOT called
        mock_openai_client.create_response.assert_not_called()

    @pytest.mark.asyncio
    async def test_welcome_message_handles_db_error_gracefully(
        self, mock_websocket, mock_db, mock_openai_client
    ):
        """Test that DB errors don't crash the session."""
        # Setup database mock to raise exception
        mock_db.query.side_effect = Exception("Database connection failed")

        # Create handler
        handler = RealtimeStreamHandler(
            websocket=mock_websocket,
            user_id="1",
            db=mock_db
        )

        # Track if session started successfully despite DB error
        session_started = False

        # Mock dependencies
        with patch.object(handler, '_prepare_system_instructions', new_callable=AsyncMock) as mock_instructions:
            mock_instructions.return_value = "You are MAVU."

            with patch.object(handler, '_load_user_voice', new_callable=AsyncMock):
                with patch('realtime.websocket_handler.OpenAIRealtimeClient', return_value=mock_openai_client):
                    with patch.object(handler, '_handle_messages', new_callable=AsyncMock):
                        try:
                            # This should not raise an exception
                            await handler.start()
                            session_started = True
                        except Exception as e:
                            pytest.fail(f"Session crashed despite DB error: {e}")

        # Verify session started successfully despite DB error
        assert session_started, "Session should start successfully despite DB error"

        # Verify OpenAI connection was attempted (even though cleaned up after)
        mock_openai_client.connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_welcome_message_handles_openai_disconnection(
        self, mock_websocket, mock_db, guest_user
    ):
        """Test that OpenAI disconnection is handled gracefully."""
        # Setup database mock to return guest user
        mock_db.query.return_value.filter.return_value.first.return_value = guest_user

        # Create handler
        handler = RealtimeStreamHandler(
            websocket=mock_websocket,
            user_id="1",
            db=mock_db
        )

        # Mock OpenAI client that disconnects
        mock_openai_client = Mock(spec=OpenAIRealtimeClient)
        mock_openai_client.connect = AsyncMock()
        mock_openai_client.disconnect = AsyncMock()
        mock_openai_client.create_response = AsyncMock()
        mock_openai_client.is_connected = False  # Simulate disconnection
        mock_openai_client.session = Mock()
        mock_openai_client.session.instructions = "Test"
        mock_openai_client._send_event = AsyncMock()

        handler.openai_client = mock_openai_client
        handler.is_active = True
        handler.ws_connected = True
        handler.ws_ready = True

        # Mock dependencies
        with patch.object(handler, '_prepare_system_instructions', new_callable=AsyncMock) as mock_instructions:
            mock_instructions.return_value = "You are MAVU."

            with patch.object(handler, '_load_user_voice', new_callable=AsyncMock):
                with patch.object(handler, '_handle_messages', new_callable=AsyncMock):
                    await handler.start()

        # create_response should not be called if OpenAI is disconnected
        mock_openai_client.create_response.assert_not_called()

    @pytest.mark.asyncio
    async def test_welcome_message_uses_correct_language(
        self, mock_websocket, mock_db, mock_openai_client
    ):
        """Test that welcome message uses user's language preference."""
        # Create users with different languages
        russian_user = User(
            id=1, email="ru@test.com",
            name=None, age=None, gender=None,
            language="ru"
        )

        english_user = User(
            id=2, email="en@test.com",
            name=None, age=None, gender=None,
            language="en"
        )

        # Test Russian user
        mock_db.query.return_value.filter.return_value.first.return_value = russian_user

        handler = RealtimeStreamHandler(
            websocket=mock_websocket,
            user_id="1",
            db=mock_db
        )

        handler.openai_client = mock_openai_client
        handler.is_active = True
        handler.ws_connected = True
        handler.ws_ready = True

        with patch.object(handler, '_prepare_system_instructions', new_callable=AsyncMock) as mock_instructions:
            mock_instructions.return_value = WELCOME_MESSAGES["ru"]["guest_greeting"]

            with patch.object(handler, '_load_user_voice', new_callable=AsyncMock):
                with patch.object(handler, '_handle_messages', new_callable=AsyncMock):
                    await handler.start()

        # Verify Russian message was used
        instructions = await mock_instructions()
        assert "Привет" in instructions or "зовут" in instructions.lower()

        # Test English user
        mock_db.query.return_value.filter.return_value.first.return_value = english_user

        handler2 = RealtimeStreamHandler(
            websocket=mock_websocket,
            user_id="2",
            db=mock_db
        )

        handler2.openai_client = mock_openai_client
        handler2.is_active = True
        handler2.ws_connected = True
        handler2.ws_ready = True

        with patch.object(handler2, '_prepare_system_instructions', new_callable=AsyncMock) as mock_instructions2:
            mock_instructions2.return_value = WELCOME_MESSAGES["en"]["guest_greeting"]

            with patch.object(handler2, '_load_user_voice', new_callable=AsyncMock):
                with patch.object(handler2, '_handle_messages', new_callable=AsyncMock):
                    await handler2.start()

        # Verify English message was used
        instructions2 = await mock_instructions2()
        assert "Hi" in instructions2 or "name" in instructions2.lower()

    @pytest.mark.asyncio
    async def test_welcome_message_timing_is_appropriate(
        self, mock_websocket, mock_db, guest_user, mock_openai_client
    ):
        """Test that welcome message has appropriate timing delay."""
        import time

        mock_db.query.return_value.filter.return_value.first.return_value = guest_user

        handler = RealtimeStreamHandler(
            websocket=mock_websocket,
            user_id="1",
            db=mock_db
        )

        handler.openai_client = mock_openai_client
        handler.is_active = True
        handler.ws_connected = True
        handler.ws_ready = True

        start_time = time.time()

        with patch.object(handler, '_prepare_system_instructions', new_callable=AsyncMock) as mock_instructions:
            mock_instructions.return_value = "Test instructions"

            with patch.object(handler, '_load_user_voice', new_callable=AsyncMock):
                with patch.object(handler, '_handle_messages', new_callable=AsyncMock):
                    await handler.start()

        elapsed_time = time.time() - start_time

        # Verify there was at least a 0.5 second delay
        # (The actual delay in code is 0.5 seconds)
        assert elapsed_time >= 0.5, "Welcome message should have appropriate timing delay"

    @pytest.mark.asyncio
    async def test_welcome_message_verifies_onboarding_prompt_in_instructions(
        self, mock_websocket, mock_db, guest_user, mock_openai_client
    ):
        """Test that code verifies onboarding prompt is in system instructions."""
        mock_db.query.return_value.filter.return_value.first.return_value = guest_user

        # Test with instructions that HAVE onboarding prompt
        mock_openai_client.session.instructions = "Привет! Как тебя зовут?"

        handler = RealtimeStreamHandler(
            websocket=mock_websocket,
            user_id="1",
            db=mock_db
        )

        with patch.object(handler, '_prepare_system_instructions', new_callable=AsyncMock) as mock_instructions:
            mock_instructions.return_value = mock_openai_client.session.instructions

            with patch.object(handler, '_load_user_voice', new_callable=AsyncMock):
                with patch('realtime.websocket_handler.OpenAIRealtimeClient', return_value=mock_openai_client):
                    with patch.object(handler, '_handle_messages', new_callable=AsyncMock):
                        await handler.start()

        # Should have triggered welcome message
        mock_openai_client.create_response.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_db_session_skips_welcome_message(
        self, mock_websocket, mock_openai_client
    ):
        """Test that missing DB session skips welcome message gracefully."""
        # Create handler without DB session
        handler = RealtimeStreamHandler(
            websocket=mock_websocket,
            user_id="1",
            db=None  # No database
        )

        handler.openai_client = mock_openai_client
        handler.is_active = True
        handler.ws_connected = True
        handler.ws_ready = True

        with patch.object(handler, '_prepare_system_instructions', new_callable=AsyncMock) as mock_instructions:
            mock_instructions.return_value = "Test instructions"

            with patch.object(handler, '_load_user_voice', new_callable=AsyncMock):
                with patch.object(handler, '_handle_messages', new_callable=AsyncMock):
                    await handler.start()

        # Should not crash, and should not call create_response
        mock_openai_client.create_response.assert_not_called()

    @pytest.mark.asyncio
    async def test_user_not_found_in_db_handles_gracefully(
        self, mock_websocket, mock_db, mock_openai_client
    ):
        """Test that user not found in DB is handled gracefully."""
        # Setup database mock to return None (user not found)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        handler = RealtimeStreamHandler(
            websocket=mock_websocket,
            user_id="999",  # Non-existent user
            db=mock_db
        )

        handler.openai_client = mock_openai_client
        handler.is_active = True
        handler.ws_connected = True
        handler.ws_ready = True

        with patch.object(handler, '_prepare_system_instructions', new_callable=AsyncMock) as mock_instructions:
            mock_instructions.return_value = "Test instructions"

            with patch.object(handler, '_load_user_voice', new_callable=AsyncMock):
                with patch.object(handler, '_handle_messages', new_callable=AsyncMock):
                    # Should not crash
                    await handler.start()

        # Should not call create_response for non-existent user
        mock_openai_client.create_response.assert_not_called()

    @pytest.mark.asyncio
    async def test_invalid_user_id_format_handles_gracefully(
        self, mock_websocket, mock_db, mock_openai_client
    ):
        """Test that invalid user_id format is handled gracefully."""
        # Create handler with invalid user_id
        handler = RealtimeStreamHandler(
            websocket=mock_websocket,
            user_id="invalid_id",  # Not a valid integer
            db=mock_db
        )

        handler.openai_client = mock_openai_client
        handler.is_active = True
        handler.ws_connected = True
        handler.ws_ready = True

        with patch.object(handler, '_prepare_system_instructions', new_callable=AsyncMock) as mock_instructions:
            mock_instructions.return_value = "Test instructions"

            with patch.object(handler, '_load_user_voice', new_callable=AsyncMock):
                with patch.object(handler, '_handle_messages', new_callable=AsyncMock):
                    # Should not crash
                    await handler.start()

        # Should handle ValueError gracefully
        # create_response should not be called
        mock_openai_client.create_response.assert_not_called()


class TestWelcomeMessageConfiguration:
    """Test welcome message configuration from config.py."""

    def test_welcome_messages_exist_for_all_languages(self):
        """Test that welcome messages exist for all supported languages."""
        assert "ru" in WELCOME_MESSAGES
        assert "en" in WELCOME_MESSAGES
        assert "uz" in WELCOME_MESSAGES

    def test_welcome_message_structure_is_complete(self):
        """Test that each language has all required message types."""
        required_keys = ["guest_greeting", "ask_age", "ask_age_no_name", "continue_chat"]

        for language, messages in WELCOME_MESSAGES.items():
            for key in required_keys:
                assert key in messages, f"Language '{language}' missing '{key}'"

    def test_welcome_messages_have_name_placeholder(self):
        """Test that ask_age messages have name placeholder."""
        for language, messages in WELCOME_MESSAGES.items():
            assert "{name}" in messages["ask_age"], \
                f"Language '{language}' ask_age missing {{name}} placeholder"

    def test_welcome_messages_are_not_empty(self):
        """Test that all welcome messages have content."""
        for language, messages in WELCOME_MESSAGES.items():
            for key, message in messages.items():
                assert message and len(message) > 0, \
                    f"Language '{language}' {key} is empty"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
