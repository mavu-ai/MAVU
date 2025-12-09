"""Telegram Web App utilities for validation and authentication."""
import hmac
import hashlib
import json
from typing import Optional, Dict, Any
from urllib.parse import parse_qsl
import structlog

from config import settings

logger = structlog.get_logger()


def validate_telegram_init_data(init_data: str) -> Optional[Dict[str, Any]]:
    """
    Validate Telegram Web App initData.

    This function validates the initData string sent from Telegram Web App
    to ensure it's authentic and hasn't been tampered with.

    Args:
        init_data: The initData string from Telegram Web App

    Returns:
        Dict with validated data if valid, None otherwise

    Security:
        Uses HMAC-SHA256 to verify the data signature against bot token
    """
    if not settings.telegram_bot_token:
        logger.error("Telegram bot token not configured")
        return None

    try:
        # Parse the init_data string into a dictionary
        parsed_data = dict(parse_qsl(init_data))

        # Extract the hash (signature) from the data
        received_hash = parsed_data.pop('hash', None)
        if not received_hash:
            logger.warning("No hash found in initData")
            return None

        # Create the data-check-string
        # Sort keys alphabetically and join with newlines
        data_check_string = '\n'.join(
            f"{k}={v}" for k, v in sorted(parsed_data.items())
        )

        # Create the secret key using HMAC-SHA256 of "WebAppData" and bot token
        secret_key = hmac.new(
            key=b"WebAppData",
            msg=settings.telegram_bot_token.encode(),
            digestmod=hashlib.sha256
        ).digest()

        # Calculate the hash of data-check-string using the secret key
        calculated_hash = hmac.new(
            key=secret_key,
            msg=data_check_string.encode(),
            digestmod=hashlib.sha256
        ).hexdigest()

        # Compare the hashes
        if not hmac.compare_digest(calculated_hash, received_hash):
            logger.warning("Invalid hash in initData", received=received_hash[:10])
            return None

        # Parse user data if present
        result = parsed_data.copy()
        if 'user' in result:
            try:
                result['user'] = json.loads(result['user'])
            except json.JSONDecodeError:
                logger.warning("Failed to parse user data")
                return None

        logger.info(
            "Successfully validated Telegram initData",
            user_id=result.get('user', {}).get('id') if isinstance(result.get('user'), dict) else None
        )

        return result

    except Exception as e:
        logger.error("Error validating Telegram initData", error=str(e))
        return None


def extract_user_info(validated_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extract user information from validated initData.

    Args:
        validated_data: Validated data from validate_telegram_init_data

    Returns:
        Dict with user information or None
    """
    if not validated_data or 'user' not in validated_data:
        return None

    user_data = validated_data['user']
    if not isinstance(user_data, dict):
        return None

    return {
        'telegram_id': user_data.get('id'),
        'first_name': user_data.get('first_name'),
        'last_name': user_data.get('last_name'),
        'username': user_data.get('username'),
        'language_code': user_data.get('language_code', 'en'),
        'is_premium': user_data.get('is_premium', False),
        'photo_url': user_data.get('photo_url')
    }


def validate_telegram_webapp_request(
        init_data: str
) -> tuple[bool, Optional[Dict[str, Any]]]:
    """
    Validate a Telegram Web App request.

    This is a convenience function that combines validation and extraction.

    Args:
        init_data: The initData string from Telegram Web App

    Returns:
        Tuple of (is_valid, user_info)
    """
    validated_data = validate_telegram_init_data(init_data)
    if not validated_data:
        return False, None

    user_info = extract_user_info(validated_data)
    if not user_info:
        return False, None

    return True, user_info
