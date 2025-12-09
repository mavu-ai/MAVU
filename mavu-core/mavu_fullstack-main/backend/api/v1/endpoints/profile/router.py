"""User profile router."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import structlog

from api.dependencies import get_db, get_current_user
from models.user import User

from .schemas import (
    UserProfileResponse,
    UserUpdateRequest,
    UserPreferencesResponse,
    UserPreferencesUpdateRequest,
)

logger = structlog.get_logger()

router = APIRouter()


@router.get("/me", response_model=UserProfileResponse)
async def get_current_user_profile(
        current_user: User = Depends(get_current_user)
):
    """
    Get current user profile.

    Returns complete profile information for the authenticated user.
    """
    return UserProfileResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        name=current_user.name,
        full_name=None,  # User model doesn't have full_name, using name instead
        age=current_user.age,
        gender=current_user.gender,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        is_admin=current_user.is_admin,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )


@router.patch("/me", response_model=UserProfileResponse)
async def update_profile(
        update: UserUpdateRequest,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Update current user profile.

    Allows updating username, email, name, age, and gender.
    """
    try:
        # Merge user into current session if needed
        db_user = db.merge(current_user)

        # Update fields
        if update.username is not None:
            # Check if username is already taken
            existing = db.query(User).filter(
                User.username == update.username,
                User.id != db_user.id
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )
            db_user.username = update.username

        if update.email is not None:
            # Check if email is already taken
            existing = db.query(User).filter(
                User.email == update.email,
                User.id != db_user.id
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already taken"
                )
            db_user.email = update.email

        if update.name is not None:
            db_user.name = update.name

        if update.age is not None:
            if update.age < 0 or update.age > 150:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid age"
                )
            db_user.age = update.age

        if update.gender is not None:
            db_user.gender = update.gender

        db.commit()
        db.refresh(db_user)

        logger.info("Profile updated", user_id=db_user.id)

        return UserProfileResponse(
            id=db_user.id,
            email=db_user.email,
            username=db_user.username,
            name=db_user.name,
            full_name=None,
            age=db_user.age,
            gender=db_user.gender,
            is_active=db_user.is_active,
            is_verified=db_user.is_verified,
            is_admin=db_user.is_admin,
            created_at=db_user.created_at,
            updated_at=db_user.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update profile", user_id=current_user.id, error=str(e))
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}"
        )


@router.delete("/me")
async def delete_profile(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Deactivate current user account.

    This marks the account as inactive rather than deleting it permanently.
    """
    try:
        # Merge user into current session if needed
        db_user = db.merge(current_user)
        db_user.is_active = False
        db.commit()

        logger.info("Profile deactivated", user_id=db_user.id)

        return {
            "success": True,
            "message": "Account deactivated successfully"
        }

    except Exception as e:
        logger.error("Failed to deactivate profile", user_id=current_user.id, error=str(e))
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deactivate account: {str(e)}"
        )


@router.get("/preferences", response_model=UserPreferencesResponse)
async def get_preferences(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Get user preferences.

    Returns language, night mode, skin settings, and UI theme mode.

    CRITICAL FIX: Always fetch fresh data from database to avoid cache issues.
    """
    try:
        # CRITICAL FIX: Query user from database to get latest values
        # Don't use refresh on potentially detached object
        db_user = db.query(User).filter(User.id == current_user.id).first()
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        logger.info(
            "Fetched user preferences",
            user_id=db_user.id,
            ui_mode=db_user.ui_mode,
            language=db_user.language
        )

        return UserPreferencesResponse(
            language=db_user.language or "en",
            night_mode=db_user.night_mode or False,
            skin_id=db_user.skin_id or 1,
            ui_mode=db_user.ui_mode or "system"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to fetch preferences", user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch preferences: {str(e)}"
        )


@router.patch("/preferences", response_model=UserPreferencesResponse)
async def update_preferences(
        update: UserPreferencesUpdateRequest,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Update user preferences.

    Allows updating language, night mode, skin settings, and UI theme mode.
    """
    try:
        # Merge user into current session if needed
        db_user = db.merge(current_user)

        if update.language is not None:
            db_user.language = update.language

        if update.night_mode is not None:
            db_user.night_mode = update.night_mode

        if update.skin_id is not None:
            if update.skin_id < 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid skin ID"
                )
            db_user.skin_id = update.skin_id

        if update.ui_mode is not None:
            if update.ui_mode not in ["light", "dark", "system"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid UI mode. Must be 'light', 'dark', or 'system'"
                )
            db_user.ui_mode = update.ui_mode

        # CRITICAL FIX: Ensure changes are flushed before commit
        db.flush()
        db.commit()
        db.refresh(db_user)

        logger.info(
            "Preferences updated successfully",
            user_id=db_user.id,
            ui_mode=db_user.ui_mode,
            language=db_user.language,
            night_mode=db_user.night_mode,
            skin_id=db_user.skin_id
        )

        return UserPreferencesResponse(
            language=db_user.language or "en",
            night_mode=db_user.night_mode if db_user.night_mode is not None else False,
            skin_id=db_user.skin_id or 1,
            ui_mode=db_user.ui_mode or "system"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update preferences", user_id=current_user.id, error=str(e))
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update preferences: {str(e)}"
        )
