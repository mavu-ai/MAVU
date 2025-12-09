"""
Test error handling in WebSocket handler.

Tests that OpenAI buffer validation errors are properly suppressed
and don't reach the client as error messages.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.realtime.websocket_handler import RealtimeStreamHandler


@pytest.mark.asyncio
async def test_empty_buffer_error_suppressed():
    """Test that empty buffer errors from OpenAI are suppressed and converted to friendly messages."""

    # Create mock websocket and dependencies
    mock_websocket = AsyncMock()
    mock_db = MagicMock()
    user_id = "test-user-123"

    # Create handler instance
    handler = RealtimeStreamHandler(
        websocket=mock_websocket,
        user_id=user_id,
        db=mock_db
    )

    # Mock the _send_to_client method to capture what's sent
    sent_messages = []

    async def capture_send(message):
        sent_messages.append(message)

    handler._send_to_client = AsyncMock(side_effect=capture_send)

    # Test Case 1: Empty buffer error with exact error code
    error_1 = {
        "type": "invalid_request_error",
        "code": "input_audio_buffer_commit_empty",
        "message": "Error committing input audio buffer: buffer too small. Expected at least 100ms of audio, but buffer only has 0.00ms of audio.",
        "param": None,
        "event_id": None
    }

    await handler._handle_error(error_1)

    # Should have sent a response.done message, NOT an error
    assert len(sent_messages) == 1
    assert sent_messages[0]["type"] == "response.done"
    assert sent_messages[0]["status"] == "insufficient_audio"
    assert "error" not in sent_messages[0]["type"]

    # Reset for next test
    sent_messages.clear()

    # Test Case 2: Buffer too small error with different format
    error_2 = {
        "type": "invalid_request_error",
        "code": "buffer_validation_error",
        "message": "Buffer too small: expected 100ms but got 0.00ms"
    }

    await handler._handle_error(error_2)

    # Should still be suppressed
    assert len(sent_messages) == 1
    assert sent_messages[0]["type"] == "response.done"
    assert sent_messages[0]["status"] == "insufficient_audio"

    # Reset for next test
    sent_messages.clear()

    # Test Case 3: Other errors should NOT be suppressed
    error_3 = {
        "type": "server_error",
        "code": "internal_error",
        "message": "Internal server error"
    }

    await handler._handle_error(error_3)

    # Should have sent an actual error message
    assert len(sent_messages) == 1
    assert sent_messages[0]["type"] == "error"


@pytest.mark.asyncio
async def test_various_buffer_error_formats():
    """Test that various formats of buffer errors are all caught."""

    mock_websocket = AsyncMock()
    mock_db = MagicMock()
    user_id = "test-user-123"

    handler = RealtimeStreamHandler(
        websocket=mock_websocket,
        user_id=user_id,
        db=mock_db
    )

    sent_messages = []

    async def capture_send(message):
        sent_messages.append(message)

    handler._send_to_client = AsyncMock(side_effect=capture_send)

    # Test various error formats that should be suppressed
    test_errors = [
        {"code": "input_audio_buffer_commit_empty", "message": "Any message"},
        {"code": "other", "message": "buffer too small"},
        {"code": "other", "message": "Buffer has 0.00ms of audio"},
        {"code": "other", "message": "BUFFER TOO SMALL in caps"},
    ]

    for error in test_errors:
        sent_messages.clear()
        await handler._handle_error(error)

        # All should be suppressed and converted to response.done
        assert len(sent_messages) == 1
        assert sent_messages[0]["type"] == "response.done"
        assert sent_messages[0]["status"] == "insufficient_audio"


@pytest.mark.asyncio
async def test_metrics_tracking():
    """Test that rejected commits are tracked in metrics."""

    mock_websocket = AsyncMock()
    mock_db = MagicMock()
    user_id = "test-user-123"

    handler = RealtimeStreamHandler(
        websocket=mock_websocket,
        user_id=user_id,
        db=mock_db
    )

    handler._send_to_client = AsyncMock()

    # Initial metrics
    initial_rejected = handler.metrics.get("rejected_commits", 0)

    # Send empty buffer error
    error = {
        "code": "input_audio_buffer_commit_empty",
        "message": "Buffer empty"
    }

    await handler._handle_error(error)

    # Metrics should be incremented
    assert handler.metrics["rejected_commits"] == initial_rejected + 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
