"""
Test OpenAI client error logging.

Tests that buffer validation errors are logged as INFO, not ERROR.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.realtime.openai_client import OpenAIRealtimeClient


@pytest.mark.asyncio
async def test_buffer_error_logged_as_info():
    """Test that buffer validation errors are logged as INFO, not ERROR."""

    # Create client instance
    client = OpenAIRealtimeClient()

    # Track what level errors are logged at
    logged_messages = []

    # Mock the logger
    with patch('backend.realtime.openai_client.logger') as mock_logger:
        # Capture log calls
        def capture_info(*args, **kwargs):
            logged_messages.append(('info', args, kwargs))

        def capture_error(*args, **kwargs):
            logged_messages.append(('error', args, kwargs))

        mock_logger.info = capture_info
        mock_logger.error = capture_error

        # Test Case 1: Empty buffer error should be logged as INFO
        error_data_1 = {
            "error": {
                "type": "invalid_request_error",
                "code": "input_audio_buffer_commit_empty",
                "message": "Error committing input audio buffer: buffer too small. Expected at least 100ms of audio, but buffer only has 0.00ms of audio."
            }
        }

        await client._handle_error(error_data_1)

        # Should have logged as INFO, not ERROR
        assert len(logged_messages) == 1
        assert logged_messages[0][0] == 'info'  # First item is log level
        assert 'buffer validation' in logged_messages[0][1][0].lower()

        # Reset
        logged_messages.clear()

        # Test Case 2: Other errors should still be logged as ERROR
        error_data_2 = {
            "error": {
                "type": "server_error",
                "code": "internal_error",
                "message": "Internal server error"
            }
        }

        await client._handle_error(error_data_2)

        # Should have logged as ERROR
        assert len(logged_messages) == 1
        assert logged_messages[0][0] == 'error'
        assert 'OpenAI Realtime error' in logged_messages[0][1][0]


@pytest.mark.asyncio
async def test_various_buffer_error_messages():
    """Test that various buffer error message formats are all logged as INFO."""

    client = OpenAIRealtimeClient()
    logged_levels = []

    with patch('backend.realtime.openai_client.logger') as mock_logger:
        def capture_info(*args, **kwargs):
            logged_levels.append('info')

        def capture_error(*args, **kwargs):
            logged_levels.append('error')

        mock_logger.info = capture_info
        mock_logger.error = capture_error

        # Test various error message formats
        test_errors = [
            {"error": {"code": "input_audio_buffer_commit_empty", "message": "Any message"}},
            {"error": {"code": "other", "message": "buffer too small"}},
            {"error": {"code": "other", "message": "Buffer has 0.00ms of audio"}},
            {"error": {"code": "other", "message": "BUFFER TOO SMALL"}},
        ]

        for error_data in test_errors:
            logged_levels.clear()
            await client._handle_error(error_data)

            # All should be logged as INFO
            assert len(logged_levels) == 1
            assert logged_levels[0] == 'info', f"Expected INFO but got {logged_levels[0]} for error: {error_data}"


@pytest.mark.asyncio
async def test_error_callback_still_called():
    """Test that error callback is still called even when error is suppressed from logs."""

    client = OpenAIRealtimeClient()

    # Mock callback
    callback_called = []

    async def mock_callback(error):
        callback_called.append(error)

    client.on_error = mock_callback

    # Mock logger to suppress actual logging
    with patch('backend.realtime.openai_client.logger'):
        # Send buffer error
        error_data = {
            "error": {
                "code": "input_audio_buffer_commit_empty",
                "message": "Buffer empty"
            }
        }

        await client._handle_error(error_data)

        # Callback should still be called
        assert len(callback_called) == 1
        assert callback_called[0]["code"] == "input_audio_buffer_commit_empty"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
