"""Text filtering utilities for chat messages."""
import re
import unicodedata


def is_emoji(char: str) -> bool:
    """Check if a character is an emoji."""
    if len(char) > 1:
        # Handle multi-character emojis (like 👨‍👩‍👧‍👦)
        return any(is_emoji(c) for c in char)

    # Check Unicode categories for emojis
    categories = unicodedata.category(char)

    # Emojis are typically in these categories
    if categories in ('So', 'Sk', 'Sm'):  # Symbols
        return True

    # Common emoji ranges
    code_point = ord(char)
    emoji_ranges = [
        (0x1F600, 0x1F64F),  # Emoticons
        (0x1F300, 0x1F5FF),  # Misc Symbols and Pictographs
        (0x1F680, 0x1F6FF),  # Transport and Map
        (0x1F1E0, 0x1F1FF),  # Regional Indicators (flags)
        (0x2600, 0x26FF),    # Misc symbols
        (0x2700, 0x27BF),    # Dingbats
        (0xFE00, 0xFE0F),    # Variation Selectors
        (0x1F900, 0x1F9FF),  # Supplemental Symbols and Pictographs
        (0x1F018, 0x1F270),  # Various asian characters
        (0x238C, 0x2454),    # Misc items
        (0x20D0, 0x20FF),    # Combining Diacritical Marks for Symbols
    ]

    return any(start <= code_point <= end for start, end in emoji_ranges)


def remove_emojis(text: str) -> str:
    """Remove all emojis from text."""
    return ''.join(char for char in text if not is_emoji(char))


def is_meaningful_text(text: str) -> bool:
    """
    Check if text contains meaningful content (not just emojis or noise).

    Returns:
        True if the text has at least some actual words/characters
        False if it's only emojis, symbols, or very short noise
    """
    if not text or len(text.strip()) == 0:
        return False

    # Remove emojis
    cleaned = remove_emojis(text).strip()

    # Check if there's meaningful content left
    if len(cleaned) < 2:  # Too short to be meaningful
        return False

    # Check if it's just punctuation or symbols
    if all(not c.isalnum() for c in cleaned.replace(' ', '')):
        return False

    # Common noise patterns to filter
    noise_patterns = [
        r'^[😀-🙏🌀-🗿🚀-🛿☀-⛿✀-➿🤀-🧿]+$',  # Only emojis (regex version)
        r'^[.,!?;:\-\s]+$',  # Only punctuation
        r'^[aа]{3,}$',  # "ааааа" or "aaaaa"
        r'^[hх]{3,}$',  # "хххх" or "hhhh"
        r'^[уу]{3,}$',  # "уууу"
        r'^м{3,}$',     # "мммм"
        r'^э{3,}$',     # "эээ"
    ]

    for pattern in noise_patterns:
        if re.match(pattern, cleaned.lower()):
            return False

    return True


def clean_chat_message(text: str) -> str:
    """
    Clean a chat message by removing emojis and normalizing whitespace.

    Returns:
        Cleaned text, or empty string if the message is not meaningful
    """
    if not text:
        return ""

    # Check if it's meaningful first
    if not is_meaningful_text(text):
        return ""

    # Remove emojis
    cleaned = remove_emojis(text)

    # Normalize whitespace
    cleaned = ' '.join(cleaned.split())

    return cleaned.strip()
