"""Test script to verify audio buffer logic."""
import asyncio
import base64
import json
from realtime.websocket_handler import RealtimeStreamHandler
from unittest.mock import Mock, AsyncMock, MagicMock


class MockWebSocket:
    """Mock WebSocket for testing."""
    def __init__(self):
        self.messages_sent = []
        self.client_state = Mock()
        self.client_state.name = "CONNECTED"

    async def accept(self):
        pass

    async def send_text(self, message):
        self.messages_sent.append(message)
        # Parse and log message type for debugging
        try:
            msg = json.loads(message)
            print(f"   → Message sent to client: {msg.get('type')}")
        except:
            pass


async def test_buffer_validation():
    """Test that buffer validation works correctly."""
    print("\n=== Testing Audio Buffer Validation ===\n")

    # Create handler with mock WebSocket
    mock_ws = MockWebSocket()
    handler = RealtimeStreamHandler(mock_ws, "test_user")

    # Mark as ready to send messages
    handler.ws_connected = True
    handler.ws_ready = True

    # Mock OpenAI client
    handler.openai_client = Mock()
    handler.openai_client.commit_audio = AsyncMock()
    handler.openai_client.is_connected = True

    print("✅ Handler initialized")
    print(f"   Min buffer duration: {handler.min_buffer_duration_ms}ms")
    print(f"   Sample rate: {handler.sample_rate}Hz")
    print(f"   Bytes per ms: {handler.bytes_per_ms}")

    # Test 0: INSTANT CLICK - Empty buffer (0ms, 0 chunks) - CRITICAL FIX TEST
    print("\n--- Test 0: INSTANT CLICK - Empty Buffer (0ms, 0 chunks) ---")
    handler.audio_buffer_size = 0
    handler.audio_buffer_duration_ms = 0.0
    handler.audio_chunk_count = 0
    handler.metrics["rejected_commits"] = 0

    print(f"   Buffer size: {handler.audio_buffer_size} bytes")
    print(f"   Buffer duration: {handler.audio_buffer_duration_ms:.2f}ms")
    print(f"   Chunk count: {handler.audio_chunk_count}")

    await handler._handle_audio_commit()

    # Check that it was rejected immediately (no OpenAI call)
    if handler.metrics["rejected_commits"] == 1 and not handler.openai_client.commit_audio.called:
        print("   ✅ PASS: Empty buffer rejected immediately (no OpenAI call)")
    else:
        print("   ❌ FAIL: Empty buffer handling incorrect")
        print(f"      Rejected commits: {handler.metrics['rejected_commits']}")
        print(f"      OpenAI called: {handler.openai_client.commit_audio.called}")

    # Check that client received response.done message
    response_done_sent = False
    for msg in mock_ws.messages_sent:
        try:
            data = json.loads(msg)
            if data.get("type") == "response.done" and data.get("status") == "no_audio":
                response_done_sent = True
                print("   ✅ PASS: Client received response.done notification")
                break
        except:
            pass

    if not response_done_sent:
        print("   ⚠️  WARNING: Client did not receive response.done notification")

    mock_ws.messages_sent.clear()
    handler.openai_client.commit_audio.reset_mock()

    # Test 1: Short audio (< 100ms) should be rejected
    print("\n--- Test 1: Short Audio (50ms) ---")
    handler.audio_buffer_size = 0
    handler.audio_buffer_duration_ms = 0.0
    handler.audio_chunk_count = 0
    handler.metrics["rejected_commits"] = 0
    mock_ws.messages_sent.clear()

    # Simulate 50ms of audio (2400 bytes at 24kHz PCM16)
    short_audio = b'\x00\x01' * 1200  # 2400 bytes = 50ms
    audio_base64 = base64.b64encode(short_audio).decode('utf-8')

    await handler._handle_audio_input({
        "audio": audio_base64,
        "chunk_id": "test1"
    })

    print(f"   Buffer size: {handler.audio_buffer_size} bytes")
    print(f"   Buffer duration: {handler.audio_buffer_duration_ms:.2f}ms")
    print(f"   Chunk count: {handler.audio_chunk_count}")

    # Add small delay to simulate grace period
    await asyncio.sleep(0.1)

    await handler._handle_audio_commit()

    if handler.metrics["rejected_commits"] == 1 and not handler.openai_client.commit_audio.called:
        print("   ✅ PASS: Short audio rejected (after grace period)")
    else:
        print("   ❌ FAIL: Short audio not rejected")
        print(f"      Rejected commits: {handler.metrics['rejected_commits']}")
        print(f"      OpenAI called: {handler.openai_client.commit_audio.called}")

    # Check for insufficient_audio notification
    insufficient_audio_sent = False
    for msg in mock_ws.messages_sent:
        try:
            data = json.loads(msg)
            if data.get("type") == "response.done" and data.get("status") == "insufficient_audio":
                insufficient_audio_sent = True
                print("   ✅ PASS: Client received insufficient_audio notification")
                break
        except:
            pass

    if not insufficient_audio_sent:
        print("   ⚠️  WARNING: Client did not receive insufficient_audio notification")

    handler.openai_client.commit_audio.reset_mock()
    mock_ws.messages_sent.clear()

    # Test 2: Long audio (> 100ms) should be accepted
    print("\n--- Test 2: Long Audio (200ms) ---")
    handler.audio_buffer_size = 0
    handler.audio_buffer_duration_ms = 0.0
    handler.audio_chunk_count = 0
    handler.metrics["audio_commits"] = 0
    handler.metrics["rejected_commits"] = 0
    handler.openai_client.commit_audio.reset_mock()
    mock_ws.messages_sent.clear()

    # Simulate 200ms of audio (9600 bytes at 24kHz PCM16)
    long_audio = b'\x00\x01' * 4800  # 9600 bytes = 200ms
    audio_base64 = base64.b64encode(long_audio).decode('utf-8')

    await handler._handle_audio_input({
        "audio": audio_base64,
        "chunk_id": "test2"
    })

    print(f"   Buffer size: {handler.audio_buffer_size} bytes")
    print(f"   Buffer duration: {handler.audio_buffer_duration_ms:.2f}ms")
    print(f"   Chunk count: {handler.audio_chunk_count}")

    # Add small delay to simulate grace period
    await asyncio.sleep(0.1)

    await handler._handle_audio_commit()

    if handler.metrics["audio_commits"] == 1 and handler.openai_client.commit_audio.called:
        print("   ✅ PASS: Long audio committed to OpenAI")
    else:
        print("   ❌ FAIL: Long audio not committed")
        print(f"      Audio commits: {handler.metrics['audio_commits']}")
        print(f"      OpenAI called: {handler.openai_client.commit_audio.called}")
        print(f"      Rejected commits: {handler.metrics['rejected_commits']}")

    # Test 3: Multiple chunks accumulation
    print("\n--- Test 3: Multiple Chunks (3 x 70ms = 210ms) ---")
    handler.audio_buffer_size = 0
    handler.audio_buffer_duration_ms = 0.0
    handler.openai_client.commit_audio.reset_mock()

    # Simulate 3 chunks of 70ms each
    chunk_audio = b'\x00\x01' * 1680  # 3360 bytes = 70ms
    audio_base64 = base64.b64encode(chunk_audio).decode('utf-8')

    for i in range(3):
        await handler._handle_audio_input({
            "audio": audio_base64,
            "chunk_id": f"test3_{i}"
        })

    print(f"   Buffer size: {handler.audio_buffer_size} bytes")
    print(f"   Buffer duration: {handler.audio_buffer_duration_ms:.2f}ms")
    print(f"   Chunks received: {handler.metrics['total_audio_chunks']}")

    await handler._handle_audio_commit()

    if handler.metrics["audio_commits"] == 2 and handler.audio_buffer_duration_ms == 0:
        print("   ✅ PASS: Multiple chunks accumulated and committed, buffer reset")
    else:
        print("   ❌ FAIL: Accumulation or reset failed")

    # Test 4: Buffer reset after commit
    print("\n--- Test 4: Buffer Reset ---")
    if handler.audio_buffer_size == 0 and handler.audio_buffer_duration_ms == 0.0:
        print("   ✅ PASS: Buffer correctly reset after commit")
    else:
        print("   ❌ FAIL: Buffer not reset")
        print(f"   Buffer size: {handler.audio_buffer_size}")
        print(f"   Buffer duration: {handler.audio_buffer_duration_ms}")

    # Summary
    print("\n=== Test Summary ===")
    print(f"Total audio commits: {handler.metrics['audio_commits']}")
    print(f"Rejected commits: {handler.metrics['rejected_commits']}")
    print(f"Total chunks processed: {handler.metrics['total_audio_chunks']}")

    print("\n✅ All tests completed!")


if __name__ == "__main__":
    asyncio.run(test_buffer_validation())
