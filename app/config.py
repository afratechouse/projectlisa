from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    APP_NAME: str = "Project Lisa"
    APP_ENV: str = "development"
    PORT: int = 8000
    DEBUG: bool = True

    # Security
    AUTHORIZED_PHONE_NUMBER: str = "8801XXXXXXXXX"
    MASTER_PIN_HASH: str = ""
    HMAC_SECRET_KEY: str = "default_secret_key"

    # Gemini
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-pro"

    # Evolution API
    EVOLUTION_API_BASE_URL: str = "http://localhost:8080"
    EVOLUTION_API_KEY: str = "lisa_secret_evolution_key"
    EVOLUTION_INSTANCE_NAME: str = "lisa"

    # Voice
    DEEPGRAM_API_KEY: Optional[str] = None
    ELEVENLABS_API_KEY: Optional[str] = None
    ELEVENLABS_VOICE_ID: str = "21m00Tcm4TlvDq8ikWAM"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None

    # Qdrant
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_API_KEY: Optional[str] = None

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
