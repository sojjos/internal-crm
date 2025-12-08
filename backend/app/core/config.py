"""Application configuration settings."""
import json
from typing import Optional, List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "SME Management"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "change-this-secret-key-in-production"

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/sme_management"

    # JWT Authentication
    JWT_SECRET_KEY: str = "change-this-jwt-secret-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hours

    # CORS - stored as comma-separated string in .env
    CORS_ORIGINS: Union[List[str], str] = "http://localhost:3000,http://localhost:5173"

    # File uploads
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10 MB

    # PayPal
    PAYPAL_MODE: str = "sandbox"  # sandbox or live
    PAYPAL_CLIENT_ID: Optional[str] = None
    PAYPAL_CLIENT_SECRET: Optional[str] = None

    # Peppol
    PEPPOL_ENABLED: bool = False
    PEPPOL_PARTICIPANT_ID: Optional[str] = None
    PEPPOL_API_URL: Optional[str] = None
    PEPPOL_API_KEY: Optional[str] = None

    # Email (SMTP)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: Optional[str] = None
    SMTP_TLS: bool = True

    # Company defaults (can be overridden in database)
    DEFAULT_CURRENCY: str = "EUR"
    DEFAULT_VAT_RATE: float = 21.0
    DEFAULT_PAYMENT_TERMS: int = 30  # days

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            # Try JSON first (for array format)
            if v.startswith("["):
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            # Otherwise split by comma
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()
