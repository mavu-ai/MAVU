"""Schemas for authentication endpoints."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class RegisterRequest(BaseModel):
    """Request schema for guest registration with promo code."""
    promo_code: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Active promo code required for registration"
    )


class RegisterResponse(BaseModel):
    """Response schema for successful guest registration."""
    user_id: int
    session_token: str
    status: str = "guest"
    created_at: datetime
    message: str = "Guest user created successfully"

    model_config = ConfigDict(from_attributes=True)


class ValidateResponse(BaseModel):
    """Response schema for session validation."""
    valid: bool
    user_id: Optional[int] = None
    email: Optional[str] = None
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    is_guest: bool = True
    is_registered: bool = False
    message: str = "Session is valid"

    model_config = ConfigDict(from_attributes=True)
