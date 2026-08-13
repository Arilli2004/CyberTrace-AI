"""
Application Configuration — CyberTrace AI
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import os


class Settings(BaseSettings):
    # ─── Application ─────────────────────────────────────────────────────────
    APP_NAME: str = "CyberTrace AI"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "change-this-secret-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # ─── Database ─────────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://cybertrace:cybertrace123@localhost:5432/cybertrace_db"
    POSTGRES_USER: str = "cybertrace"
    POSTGRES_PASSWORD: str = "cybertrace123"
    POSTGRES_DB: str = "cybertrace_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    # ─── Redis ────────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ─── OpenAI / Local Gemma AI (LM Studio) ──────────────────────────────────
    OPENAI_API_KEY: str = "lm-studio"
    OPENAI_BASE_URL: str = "http://127.0.0.1:1234/v1"
    OPENAI_MODEL: str = "google/gemma-4-e4b"
    OPENAI_MAX_TOKENS: int = 4096

    # ─── File Storage ─────────────────────────────────────────────────────────
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 500
    ALLOWED_EXTENSIONS: List[str] = ["evtx", "log", "csv", "json", "xml"]

    # ─── Server ───────────────────────────────────────────────────────────────
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
