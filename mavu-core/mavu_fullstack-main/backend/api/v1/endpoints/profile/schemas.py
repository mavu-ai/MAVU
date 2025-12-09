"""User profile schemas."""
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class UserProfileResponse(BaseModel):
    """User profile response."""
    id: int
    email: Optional[str]
    username: Optional[str]
    name: Optional[str]
    full_name: Optional[str]
    age: Optional[int]
    gender: Optional[str]
    is_active: bool
    is_verified: bool
    is_admin: bool
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class UserUpdateRequest(BaseModel):
    """User profile update request."""
    username: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    full_name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None


class UserPreferencesResponse(BaseModel):
    """User preferences response."""
    language: str
    night_mode: bool
    skin_id: int
    ui_mode: str

    model_config = ConfigDict(from_attributes=True)


class UserPreferencesUpdateRequest(BaseModel):
    """User preferences update request."""
    language: Optional[str] = None
    night_mode: Optional[bool] = None
    skin_id: Optional[int] = None
    ui_mode: Optional[str] = None
