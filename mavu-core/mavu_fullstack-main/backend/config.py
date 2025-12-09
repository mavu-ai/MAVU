"""Application configuration settings."""
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # OpenAI Configuration
    openai_api_key: str
    openai_model: str = "gpt-4o-realtime-preview"  # For realtime voice interactions
    openai_chat_model: str = "gpt-4-turbo-preview"  # For chat completions (extraction, etc.)
    openai_embedding_model: str = "text-embedding-3-small"
    openai_realtime_url: str = "wss://api.openai.com/v1/realtime"

    # PostgreSQL Configuration
    database_url: str = "postgresql://mavuai:mavuai_password@localhost:5432/mavuai"
    postgres_db: str = "mavuai"
    postgres_user: str = "mavuai"
    postgres_password: str = "mavuai_password"

    # Weaviate Configuration
    weaviate_url: str = "http://localhost:8080"
    weaviate_api_key: Optional[str] = None

    # Redis Configuration
    redis_url: str = "redis://localhost:6379"
    redis_cache_ttl: int = 3600

    # Application Settings
    app_name: str = "MavuAI"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = True

    # Security
    secret_key: str = "change_this_in_production"

    # Admin Settings
    admin_secret_key: str = "change_this_in_production"

    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_period: int = 60

    # CORS Settings - Hardcoded for production
    @property
    def cors_origins(self) -> List[str]:
        """CORS allowed origins."""
        return [
            "https://ai.mavu.app",
            "https://mavu.app",
            "https://mavu.aey-inc.uz",
            "https://aey-inc.uz",
            "http://localhost:3000",
            "http://localhost:5173"
        ]

    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]

    # Server Settings
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True

    # RAG Settings
    rag_chunk_size: int = 500
    rag_chunk_overlap: int = 50
    rag_top_k_user: int = 5
    rag_top_k_app: int = 5

    # Telegram Bot Settings
    telegram_bot_token: Optional[str] = None
    telegram_webhook_url: Optional[str] = None  # e.g., https://yourdomain.com/api/v1/webhook/telegram
    telegram_webhook_secret: Optional[str] = None  # Secret token for webhook validation
    telegram_webapp_url: Optional[str] = None  # Your Web App URL

    # Payme Payment Gateway Settings
    payme_host: str = "https://checkout.paycom.uz"
    payme_merchant_id: Optional[str] = None
    payme_login: Optional[str] = None  # Payme merchant login (Paycom ID)
    payme_key: Optional[str] = None  # Payme secret key for authentication
    app_price: int = 100_000  # Default price in tiyin (1 UZS = 100 tiyin)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra env vars like PROJECT_NAME
    )


# Character Skins Configuration
# Valid OpenAI Realtime API voices: alloy, ash, ballad, coral, echo, sage, shimmer, verse, marin, cedar
SKINS = {
    1: {  # Alex - Male
        "name": "Alex",
        "gender": "male",
        "voice": "echo",
        "description": "Clear and articulate male voice"
    },
    2: {  # Maya - Female
        "name": "Maya",
        "gender": "female",
        "voice": "shimmer",
        "description": "Warm and expressive female voice"
    },
    3: {  # Robo - Neutral
        "name": "Robo",
        "gender": "neutral",
        "voice": "alloy",
        "description": "Balanced and robotic neutral voice"
    },
    4: {  # Ash - Male
        "name": "Ash",
        "gender": "male",
        "voice": "ash",
        "description": "Strong and confident male voice"
    },
    5: {  # Melody - Female
        "name": "Melody",
        "gender": "female",
        "voice": "ballad",
        "description": "Lyrical and musical female voice"
    },
    6: {  # Coral - Female
        "name": "Coral",
        "gender": "female",
        "voice": "coral",
        "description": "Bright and cheerful female voice"
    },
    7: {  # Sage - Male
        "name": "Sage",
        "gender": "male",
        "voice": "sage",
        "description": "Wise and calm male voice"
    },
    8: {  # Aria - Female
        "name": "Aria",
        "gender": "female",
        "voice": "verse",
        "description": "Poetic and artistic female voice"
    },
    9: {  # Marina - Female
        "name": "Marina",
        "gender": "female",
        "voice": "marin",
        "description": "Calm and flowing female voice"
    },
    10: {  # Cedar - Male
        "name": "Cedar",
        "gender": "male",
        "voice": "cedar",
        "description": "Deep and grounded male voice"
    }
}


# Welcome messages for guest users
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


# Create global settings instance
settings = Settings()
