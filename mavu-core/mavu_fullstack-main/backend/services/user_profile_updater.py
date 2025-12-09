"""
Smart user profile updater with validation logic.

This module provides safe user profile updates that:
- Validate extracted data before updating
- Don't overwrite good data with bad data
- Log all update decisions
"""

import structlog
from typing import Dict, Optional, Any
from sqlalchemy.orm import Session

from models.user import User
from services.user_info_extraction_service import UserInfoExtractionService

logger = structlog.get_logger()


class UserProfileUpdater:
    """Safely update user profiles with extracted data."""

    @classmethod
    def should_update_name(
        cls,
        current_name: Optional[str],
        extracted_name: Optional[str]
    ) -> bool:
        """
        Decide if we should update the name.

        Rules:
        1. Update if current is None and extracted is valid
        2. Update if current is invalid and extracted is valid
        3. Don't update if current is already valid
        """
        if not extracted_name:
            return False

        # Validate extracted name
        if not UserInfoExtractionService.is_valid_name(extracted_name):
            logger.debug(f"Extracted name invalid: {extracted_name}")
            return False

        # No current name - safe to update
        if not current_name:
            return True

        # Check if current name is invalid
        if not UserInfoExtractionService.is_valid_name(current_name):
            logger.info(
                f"Replacing invalid name '{current_name}' with '{extracted_name}'"
            )
            return True

        # Current name is valid - don't overwrite
        logger.info(
            f"Keeping valid name '{current_name}', ignoring '{extracted_name}'"
        )
        return False

    @classmethod
    def should_update_age(
        cls,
        current_age: Optional[int],
        extracted_age: Optional[int]
    ) -> tuple[bool, Optional[str]]:
        """
        Decide if we should update the age.

        Returns (should_update, reason)
        """
        if not extracted_age:
            return False, None

        # Validate age range
        if not (3 <= extracted_age <= 99):
            return False, f"Age {extracted_age} out of valid range"

        # No current age - safe to update
        if not current_age:
            return True, "new age"

        # Age changed - log warning but still update
        if current_age != extracted_age:
            reason = f"age changed from {current_age} to {extracted_age}"
            logger.warning(reason)
            return True, reason

        return False, "age unchanged"

    @classmethod
    def should_update_gender(
        cls,
        current_gender: Optional[str],
        extracted_gender: Optional[str]
    ) -> tuple[bool, Optional[str]]:
        """
        Decide if we should update the gender.

        Returns (should_update, reason)
        """
        if not extracted_gender:
            return False, None

        # Validate gender value
        if extracted_gender not in ['male', 'female']:
            return False, f"Invalid gender: {extracted_gender}"

        # No current gender - safe to update
        if not current_gender:
            return True, "new gender"

        # Gender already set - don't change it
        if current_gender != extracted_gender:
            logger.info(
                f"Gender already set to '{current_gender}', ignoring '{extracted_gender}'"
            )
            return False, "gender already set"

        return False, "gender unchanged"

    @classmethod
    async def update_user_profile(
        cls,
        user: User,
        user_message: str,
        assistant_response: str,
        db: Session
    ) -> Dict[str, Any]:
        """
        Update user profile with extracted data.

        Args:
            user: User model instance
            user_message: User's message
            assistant_response: Assistant's response
            db: Database session

        Returns:
            Dictionary with update results
        """
        # Store original values
        original = {
            'name': user.name,
            'age': user.age,
            'gender': user.gender
        }

        # Extract new data
        extracted = await UserInfoExtractionService.extract_from_conversation(
            user_message=user_message,
            assistant_response=assistant_response,
            current_user_info=None
        )

        logger.debug(
            "Extraction attempt",
            user_id=user.id,
            extracted=extracted,
            current=original
        )

        # Track updates
        updates = []
        changes = {}

        # Update name if appropriate
        if cls.should_update_name(original['name'], extracted.get('name')):
            user.name = extracted['name']
            updates.append(f"name='{extracted['name']}'")
            changes['name'] = {'from': original['name'], 'to': extracted['name']}

        # Update age if appropriate
        should_update_age, age_reason = cls.should_update_age(
            original['age'],
            extracted.get('age')
        )
        if should_update_age:
            user.age = extracted['age']
            updates.append(f"age={extracted['age']}")
            changes['age'] = {'from': original['age'], 'to': extracted['age']}

        # Update gender if appropriate
        should_update_gender, gender_reason = cls.should_update_gender(
            original['gender'],
            extracted.get('gender')
        )
        if should_update_gender:
            user.gender = extracted['gender']
            updates.append(f"gender='{extracted['gender']}'")
            changes['gender'] = {'from': original['gender'], 'to': extracted['gender']}

        # Try to infer gender from name if we have name but no gender
        if user.name and not user.gender:
            name_check = UserInfoExtractionService.extract_from_text_simple(user.name)
            if name_check.get('gender'):
                user.gender = name_check['gender']
                updates.append(f"gender='{name_check['gender']}' (from name)")
                changes['gender'] = {'from': None, 'to': name_check['gender']}

        # Commit if changes were made
        if updates:
            try:
                db.flush()
                db.commit()
                db.refresh(user)

                logger.info(
                    "✅ User profile updated",
                    user_id=user.id,
                    updates=", ".join(updates),
                    final=f"name={user.name!r}, age={user.age}, gender={user.gender!r}"
                )

                return {
                    'success': True,
                    'updated': True,
                    'changes': changes,
                    'updates': updates,
                    'profile': {
                        'name': user.name,
                        'age': user.age,
                        'gender': user.gender
                    }
                }

            except Exception as e:
                logger.error("Failed to commit profile updates", error=str(e))
                db.rollback()
                return {
                    'success': False,
                    'updated': False,
                    'error': str(e)
                }

        else:
            logger.debug("No profile updates needed", user_id=user.id)
            return {
                'success': True,
                'updated': False,
                'profile': {
                    'name': user.name,
                    'age': user.age,
                    'gender': user.gender
                }
            }
