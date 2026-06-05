from functools import lru_cache

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "Ding AI Service"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "local"
    DEBUG: bool = False

    ALLOWED_ORIGINS: list[str] = Field(default_factory=lambda: ["*"])

    DATABASE_URL: str = "postgresql+asyncpg://ding_ai:ding_ai_pass@localhost:5433/ding_ai_db"
    REDIS_URL: str = "redis://localhost:6380"
    REDIS_CHAT_TTL: int = 60 * 30

    JWT_SECRET: str = "change-me"
    JWT_ALGORITHMS: list[str] = Field(default_factory=lambda: ["HS256"])
    # Ding platform access tokens use `userId`; `sub` is still accepted via fallback in security.py
    JWT_PLATFORM_USER_ID_CLAIM: str = "userId"

    SERVICE_API_KEY: str = "change-me"
    SERVICE_API_KEY_HEADER: str = "X-API-Key"

    OLLAMA_BASE_URL: AnyHttpUrl = "http://localhost:11434"
    OLLAMA_MODEL: str = "gemma3:4b"
    OLLAMA_TIMEOUT: float = 60.0
    OLLAMA_MAX_CONTEXT_MESSAGES: int = 20

    TTS_ENABLED: bool = True
    TTS_LANG_CODE: str = "a"
    TTS_SPEED: float = 1.28
    TTS_RETURN_VISEMES_DEFAULT: bool = True

    MAX_PAGE_SIZE: int = 100


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

