"""Test response completion handling to ensure processing state is properly cleared."""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from realtime.websocket_handler import RealtimeStreamHandler
from models.user import User


@pytest.mark.asyncio
async def test_response_complete_sends_done_message():
    """
    Test that _handle_response_complete sends response.done to client.

    This is critical for clearing the UI processing state after a conversation ends.

    Bug fix: Previously the backend would process the response but never notify
    the frontend that processing was complete, leaving the microphone button
    stuck in a loading state.
    """
    # Create mock WebSocket
    mock_websocket = Mock()
    mock_websocket.accept = AsyncMock()
    mock_websocket.send_text = AsyncMock()
    mock_websocket.client_state = Mock()
    mock_websocket.client_state.name = "CONNECTED"
    mock_websocket.application_state = Mock()
    mock_websocket.application_state.name = "CONNECTED"

    # Create mock database session
    mock_db = Mock()

    # Create handler instance
    handler = RealtimeStreamHandler(
        websocket=mock_websocket,
        user_id="test_user_123",
        db=mock_db
    )

    # Mark as connected and ready
    handler.ws_connected = True
    handler.ws_ready = True

    # Set up a conversation that completed
    handler.current_user_message = "Hello, how are you?"
    handler.current_assistant_response = "I'm doing well, thank you for asking!"

    # Mock database user
    mock_user = Mock(spec=User)
    mock_user.id = 123
    mock_db.query.return_value.filter.return_value.first.return_value = mock_user

    # Call the handler
    await handler._handle_response_complete({})

    # Verify response.done was sent to client
    assert mock_websocket.send_text.called

    # Get all calls to send_text
    calls = mock_websocket.send_text.call_args_list

    # Check if any call contains response.done
    response_done_sent = False
    for call in calls:
        import json
        message = json.loads(call[0][0])
        if message.get("type") == "response.done":
            response_done_sent = True
            assert message.get("status") in ["completed", "error"]
            break

    assert response_done_sent, "response.done message was not sent to client"

    # Verify conversation state was reset
    assert handler.current_user_message == ""
    assert handler.current_assistant_response == ""


@pytest.mark.asyncio
async def test_response_complete_sends_done_on_error():
    """
    Test that response.done is sent even when an error occurs during processing.

    This ensures the UI can recover from backend errors and doesn't get stuck
    in a perpetual loading state.
    """
    # Create mock WebSocket
    mock_websocket = Mock()
    mock_websocket.accept = AsyncMock()
    mock_websocket.send_text = AsyncMock()
    mock_websocket.client_state = Mock()
    mock_websocket.client_state.name = "CONNECTED"
    mock_websocket.application_state = Mock()
    mock_websocket.application_state.name = "CONNECTED"

    # Create mock database session that will raise an error
    mock_db = Mock()
    mock_db.query.side_effect = Exception("Database error")

    # Create handler instance
    handler = RealtimeStreamHandler(
        websocket=mock_websocket,
        user_id="test_user_123",
        db=mock_db
    )

    # Mark as connected and ready
    handler.ws_connected = True
    handler.ws_ready = True

    # Set up a conversation
    handler.current_user_message = "Test message"
    handler.current_assistant_response = "Test response"

    # Call the handler - should not raise exception
    await handler._handle_response_complete({})

    # Verify response.done was still sent despite the error
    assert mock_websocket.send_text.called

    # Get all calls to send_text
    calls = mock_websocket.send_text.call_args_list

    # Check if any call contains response.done
    response_done_sent = False
    for call in calls:
        import json
        message = json.loads(call[0][0])
        if message.get("type") == "response.done":
            response_done_sent = True
            # Even with database errors, the handler continues and sends completed
            # This is intentional - DB errors shouldn't block the UI from recovering
            assert message.get("status") in ["completed", "error"]
            break

    assert response_done_sent, "response.done message was not sent to client even after error"

    # Verify conversation state was reset even on error
    assert handler.current_user_message == ""
    assert handler.current_assistant_response == ""


@pytest.mark.asyncio
async def test_response_complete_with_no_message():
    """
    Test that response.done is not sent when there's no user message.

    This prevents unnecessary messages when there's nothing to process.
    """
    # Create mock WebSocket
    mock_websocket = Mock()
    mock_websocket.send_text = AsyncMock()

    # Create handler instance
    handler = RealtimeStreamHandler(
        websocket=mock_websocket,
        user_id="test_user_123",
        db=None
    )

    # Mark as connected
    handler.ws_connected = True
    handler.ws_ready = True

    # No conversation data
    handler.current_user_message = ""
    handler.current_assistant_response = ""

    # Call the handler
    await handler._handle_response_complete({})

    # Verify no messages were sent since there's nothing to process
    assert not mock_websocket.send_text.called


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
