"""Application configuration"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    APP_NAME: str = "CommunityCircle"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    API_V1_PREFIX: str = "/api"

    # Database
    DATABASE_URL: str
    DATABASE_URL_SYNC: str

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    @property
    def allowed_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # SMS (Plivo)
    PLIVO_AUTH_ID: str = ""
    PLIVO_AUTH_TOKEN: str = ""
    PLIVO_PHONE_NUMBER: str = ""

    # Email (Brevo)
    BREVO_API_KEY: str = ""
    BREVO_SENDER_EMAIL: str = "noreply@communitycircle.org"
    BREVO_SENDER_NAME: str = "CommunityCircle"

    # 211 API
    TWO11_API_KEY: str = ""
    TWO11_API_URL: str = "https://api.211.org"

    # Frontend URL
    FRONTEND_URL: str = "http://localhost:5173"

    # Monitoring
    SENTRY_DSN: str = ""
    POSTHOG_API_KEY: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
