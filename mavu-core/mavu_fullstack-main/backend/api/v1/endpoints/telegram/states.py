"""FSM states for Telegram bot conversation flow."""
from aiogram.fsm.state import State, StatesGroup


class RegistrationStates(StatesGroup):
    """States for new user registration flow via Telegram bot."""

    awaiting_language = State()
    awaiting_promo_code = State()
    completed = State()
