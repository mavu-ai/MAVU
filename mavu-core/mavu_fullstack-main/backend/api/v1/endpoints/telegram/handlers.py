"""Command handlers for Telegram bot."""
import structlog
from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from models import User
from .keyboards import get_language_keyboard, get_webapp_keyboard, get_help_keyboard
from .states import RegistrationStates

logger = structlog.get_logger()

# Create router for handlers
router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """
    Handle /start command.

    Simplified flow:
    1. New users: Ask for language preference
    2. After language: Show Web App button
    3. Existing users: Show Web App button directly

    User profile info (name, age, gender) is collected conversationally during chat.
    """
    user = message.from_user
    telegram_id = user.id

    logger.info(
        "User started bot",
        telegram_id=telegram_id,
        username=user.username,
        first_name=user.first_name
    )

    # Check if user already exists in database
    from dependencies.database import SessionLocal
    db = SessionLocal()
    try:
        existing_user = db.query(User).filter(User.telegram_id == telegram_id).first()

        if existing_user:
            # Existing user - show Web App directly
            logger.info("Existing user detected", user_id=existing_user.id, telegram_id=telegram_id)

            welcome_text = (
                f"Welcome back, <b>{user.first_name}</b>! 👋\n\n"
                "Ready to continue your journey with MavuAI?\n\n"
                "Tap the button below to launch the app! 💙"
            )

            await message.answer(
                text=welcome_text,
                reply_markup=get_webapp_keyboard(existing_user)
            )
        else:
            # New user - start with language selection
            logger.info("New user detected, asking for language", telegram_id=telegram_id)

            welcome_text = (
                f"Hello, <b>{user.first_name}</b>! 👋\n\n"
                "Welcome to <b>MavuAI</b> - your AI companion that cares about you.\n\n"
                "First, please select your preferred language:"
            )

            await state.set_state(RegistrationStates.awaiting_language)
            await message.answer(
                text=welcome_text,
                reply_markup=get_language_keyboard()
            )
    finally:
        db.close()


@router.callback_query(F.data.startswith("lang:"))
async def handle_language_selection(callback: CallbackQuery, state: FSMContext):
    """
    Handle language selection callback.

    Creates user with selected language and shows Web App button.
    """
    current_state = await state.get_state()

    if current_state != RegistrationStates.awaiting_language:
        await callback.answer("Please use /start to begin", show_alert=True)
        return

    # Extract language code from callback data
    language_code = callback.data.split(":")[1]

    telegram_id = callback.from_user.id
    username = callback.from_user.username
    first_name = callback.from_user.first_name

    logger.info(
        "Language selected",
        telegram_id=telegram_id,
        language=language_code
    )

    # Language names for confirmation
    language_names = {
        "en": "English",
        "ru": "Русский",
    }

    language_name = language_names.get(language_code, language_code)

    # Create or update user
    from dependencies.database import SessionLocal
    db = SessionLocal()
    try:
        # Check if user exists (shouldn't, but handle it)
        existing_user = db.query(User).filter(User.telegram_id == telegram_id).first()

        if existing_user:
            # Update language
            existing_user.language = language_code
            db.commit()
            db.refresh(existing_user)
            user = existing_user
            logger.info("Updated existing user language", user_id=user.id, language=language_code)
        else:
            # Create new guest user (name, age, gender will be extracted during chat)
            new_user = User(
                telegram_id=telegram_id,
                username=username,
                name=None,  # Will be extracted conversationally
                age=None,  # Will be extracted conversationally
                gender=None,  # Will be extracted conversationally
                language=language_code,
                is_verified=True,  # Telegram users are pre-verified
                is_active=True
            )

            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            user = new_user

            logger.info(
                "Guest user created",
                user_id=user.id,
                telegram_id=telegram_id,
                language=language_code
            )

        success_text = (
            f"✅ Language set to <b>{language_name}</b>!\n\n"
            f"Welcome to MavuAI, {first_name}! 🎉\n\n"
            "Tap the button below to launch the app and start chatting with your AI companion!"
        )

        await state.clear()
        await callback.message.edit_text(
            text=success_text,
            reply_markup=get_webapp_keyboard(user)
        )
        await callback.answer()

    except Exception as e:
        logger.error(
            "Error during user creation",
            telegram_id=telegram_id,
            error=str(e)
        )
        db.rollback()

        error_text = (
            "❌ An error occurred. Please try again later or contact support."
        )

        await callback.message.edit_text(error_text)
        await callback.answer()
    finally:
        db.close()


# Removed promo code handler - no longer needed


@router.message(Command("help"))
async def cmd_help(message: Message):
    """
    Handle /help command.

    Provides information about bot usage and available commands.
    """
    user = message.from_user
    logger.info("User requested help", user_id=user.id, username=user.username)

    help_text = (
        "<b>MavuAI - Your AI Companion</b>\n\n"
        "<b>Available Commands:</b>\n"
        "/start - Launch MavuAI Web App\n"
        "/help - Show this help message\n\n"
        "<b>Features:</b>\n"
        "• Real-time voice conversations\n"
        "• Emotional intelligence\n"
        "• Personalized responses\n"
        "• Privacy-focused\n\n"
        "Tap the button below to get started!"
    )

    keyboard = get_help_keyboard()

    await message.answer(
        text=help_text,
        reply_markup=keyboard
    )


@router.callback_query(F.data == "config_needed")
async def callback_config_needed(callback: CallbackQuery):
    """
    Handle callback when Web App URL is not configured.

    This is a fallback handler for development/testing.
    """
    await callback.answer(
        "Web App URL is not configured. Please contact the administrator.",
        show_alert=True
    )


@router.message()
async def handle_any_message(message: Message):
    """
    Handle any other message.

    This is a catch-all handler that directs users to use the /start command.
    """
    user = message.from_user
    logger.info(
        "User sent unhandled message",
        user_id=user.id,
        message_text=message.text[:50] if message.text else None
    )

    response_text = (
        "I'm a bot that works through the Web App interface. 🤖\n\n"
        "Please use /start to launch MavuAI and start chatting with me!"
    )

    keyboard = get_webapp_keyboard()

    await message.answer(
        text=response_text,
        reply_markup=keyboard
    )
