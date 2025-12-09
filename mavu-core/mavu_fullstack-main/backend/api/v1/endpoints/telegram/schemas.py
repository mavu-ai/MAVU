"""Schemas for Telegram endpoints."""
from typing import Optional
from pydantic import BaseModel, Field


class TelegramAuthRequest(BaseModel):
    """Request schema for Telegram Web App authentication."""

    init_data: str = Field(
        ...,
        description="Telegram Web App initData for validation"
    )
    language: Optional[str] = Field(
        None,
        description="User's preferred language code (e.g., 'en', 'ru'')",
        min_length=2,
        max_length=10,
        examples=["en", "ru"]
    )


class TelegramAuthResponse(BaseModel):
    """Response schema for Telegram Web App authentication."""

    user_id: str = Field(
        ...,
        description="Unique user identifier"
    )
    telegram_id: int = Field(
        ...,
        description="Telegram user ID"
    )
    language: str = Field(
        ...,
        description="User's language preference"
    )
    username: Optional[str] = Field(
        None,
        description="Telegram username"
    )
    name: Optional[str] = Field(
        None,
        description="User's full name"
    )


class WebhookInfo(BaseModel):
    """Response schema for webhook info."""

    url: Optional[str] = Field(None, description="Current webhook URL")
    has_custom_certificate: bool = Field(
        default=False,
        description="Whether webhook uses custom certificate"
    )
    pending_update_count: int = Field(
        default=0,
        description="Number of pending updates"
    )
    last_error_date: Optional[int] = Field(
        None,
        description="Unix timestamp of last error"
    )
    last_error_message: Optional[str] = Field(
        None,
        description="Last error message"
    )


class WebhookSetupResponse(BaseModel):
    """Response schema for webhook setup."""

    success: bool = Field(..., description="Whether webhook was set successfully")
    message: str = Field(..., description="Status message")
    webhook_info: Optional[WebhookInfo] = Field(None, description="Webhook information")
