# Welcome Message System

## Overview

The Welcome Message System automatically detects guest users (users without profile information) and triggers a welcoming voice greeting upon WebSocket connection. This creates an immediate, engaging experience for new users without requiring them to speak first.

## How It Works

### 1. Guest User Detection

A user is identified as a "guest" when they have:
- `name` = NULL
- `age` = NULL
- `gender` = NULL

This is determined by the `is_guest` property in the User model:

```python
@property
def is_guest(self) -> bool:
    """Check if user is a guest (no profile information)."""
    return self.name is None and self.age is None and self.gender is None
```

### 2. Automatic Welcome Trigger

When a guest connects to the WebSocket:

1. **Session Initialization**: WebSocket connection established and OpenAI session configured
2. **Guest Detection**: System checks `user.is_guest` property
3. **Welcome Trigger**: If guest, waits 500ms then calls `openai_client.create_response()`
4. **Voice Response**: OpenAI generates and streams welcome message in selected voice
5. **User Interaction**: Microphone activates for user to respond

### 3. Multi-Language Support

Welcome messages are configured in `backend/config.py`:

```python
WELCOME_MESSAGES = {
    "ru": {
        "guest_greeting": "Привет! Я MAVU, твоя цифровая подружка. Как тебя зовут?",
        "ask_age": "Приятно познакомиться, {name}! Сколько тебе лет?",
        "ask_age_no_name": "Сколько тебе лет?",
        "continue_chat": "Отлично! Давай поговорим. О чём ты хочешь рассказать?"
    },
    "en": {
        "guest_greeting": "Hi! I'm MAVU, your digital friend. What's your name?",
        "ask_age": "Nice to meet you, {name}! How old are you?",
        "ask_age_no_name": "How old are you?",
        "continue_chat": "Great! Let's chat. What would you like to talk about?"
    },
    "uz": {
        "guest_greeting": "Salom! Men MAVU, sizning raqamli do'stingizman. Ismingiz nima?",
        "ask_age": "Tanishganimdan xursandman, {name}! Yoshingiz nechada?",
        "ask_age_no_name": "Yoshingiz nechada?",
        "continue_chat": "Ajoyib! Gaplashamiz. Nima haqida gaplashmoqchisiz?"
    }
}
```

## Implementation Details

### Backend Components

#### 1. Welcome Message Trigger (`websocket_handler.py`)

```python
# Lines 200-267: Trigger initial welcome message for guest users
if self.db:
    try:
        user = self.db.query(User).filter(User.id == int(self.user_id)).first()
        if user and user.is_guest:
            logger.info("Guest user detected - triggering welcome message")

            # Wait for OpenAI initialization
            await asyncio.sleep(0.5)

            # Trigger welcome response
            await self.openai_client.create_response(
                modalities=["text", "audio"]
            )

            logger.info("Welcome response triggered successfully")
    except Exception as e:
        logger.error(f"Failed to trigger welcome message: {e}")
        # Don't fail session - user can still speak first
```

#### 2. System Instructions Enhancement

The system instructions are dynamically updated with onboarding prompts for guest users:

```python
# user_info_extraction_service.py
if not user_name:
    prompt = f"""
    CRITICAL: You DON'T KNOW the user's name.

    YOUR TASK:
    1. In your FIRST RESPONSE, greet and ask: "{messages['guest_greeting']}"
    2. When you get the name, IMMEDIATELY ask for age
    3. After getting age, continue normal conversation
    """
```

#### 3. Profile Extraction

As the user responds, the system extracts and saves profile information:

1. **Name Extraction**: Uses regex patterns and LLM fallback
2. **Age Extraction**: Validates age between 3-99
3. **Gender Inference**: Based on name patterns
4. **Database Update**: Saves validated data only

### Frontend Handling

The frontend must handle the `response.done` message to clear processing state:

```typescript
// VoiceChat.tsx
case 'response.done':
    setIsProcessing(false)  // Enable microphone
    clearTimeout(processingTimeoutRef.current)
    break
```

## Configuration

### Customizing Welcome Messages

Edit `backend/config.py` to customize messages:

```python
WELCOME_MESSAGES = {
    "en": {
        "guest_greeting": "Hello! I'm your AI companion. What should I call you?",
        # ... other messages
    }
}
```

### Voice Selection

10 character voices are available through the SKINS configuration:

- Alex (echo)
- Maya (shimmer) - Default
- Robo (alloy)
- Ash (ash)
- Melody (ballad)
- Coral (coral)
- Sage (sage)
- Aria (verse)
- Marina (marin)
- Cedar (cedar)

## Error Handling

The system includes comprehensive error handling:

1. **Database Errors**: Logged but don't crash session
2. **OpenAI Disconnection**: Detected and logged
3. **Invalid User ID**: Caught with ValueError handling
4. **General Exceptions**: Caught with fallback to user-initiated conversation

### Expected Errors

The system suppresses certain expected errors:

- `input_audio_buffer_commit_empty`: Normal when triggering without user audio
- Buffer size errors: Expected during welcome message generation

## Testing

### Test Script

A comprehensive test is available at `backend/tests/test_welcome_message.py`:

```python
# Run the test
python backend/tests/test_welcome_message.py
```

### Test Coverage

- ✅ Guest user detection
- ✅ Welcome message triggering
- ✅ Non-guest users don't receive welcome
- ✅ Database error handling
- ✅ OpenAI disconnection handling
- ✅ Language preference respect
- ✅ Invalid user ID handling
- ✅ Timing verification

## Performance

- **Welcome Delay**: 500ms after session ready
- **Total Time**: ~1 second from connection to voice
- **Non-blocking**: All operations are async
- **Graceful Degradation**: Failures don't impact session

## Monitoring

Key log messages to monitor:

```
INFO: Guest user detected - triggering welcome message
INFO: Welcome response triggered successfully for guest user
ERROR: Failed to trigger welcome message
WARNING: Onboarding prompt NOT found in system instructions
```

## Troubleshooting

### Welcome Message Not Playing

1. **Check Logs**: Look for "Guest user detected" message
2. **Verify Guest Status**: Ensure user has NULL name, age, gender
3. **Check OpenAI Connection**: Verify "OpenAI connected successfully"
4. **System Instructions**: Check for onboarding prompt presence

### Wrong Language

1. **Check User Language**: Verify `user.language` field
2. **Default Language**: System defaults to Russian if not specified
3. **Update Config**: Ensure language exists in WELCOME_MESSAGES

### Audio Issues

1. **Frontend Audio**: Verify audio playback is initialized
2. **Voice Selection**: Check SKINS configuration
3. **Network**: Ensure adequate bandwidth for audio streaming

## Future Enhancements

Potential improvements for future versions:

1. **A/B Testing**: Test different welcome messages
2. **Personalization**: Time-based greetings (morning/evening)
3. **Retry Logic**: Automatic retry on OpenAI failures
4. **Metrics Tracking**: Success rate monitoring
5. **Dynamic Timing**: Adjust delay based on network conditions
6. **Custom Voices**: Per-user voice preferences
7. **Contextual Welcome**: Based on referral source or promo code

## Related Documentation

- [Profile Extraction](profile-extraction.md)
- [Character System](characters.md)
- [RAG Architecture](../architecture/rag-realtime-flow.md)
- [WebSocket Guide](../mobile/websocket-guide.md)