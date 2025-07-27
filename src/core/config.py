"""Core configuration settings for the AI Consultancy Platform."""

import os
import logging
from typing import Optional
from pydantic_settings import BaseSettings
from decouple import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Environment: development, staging, production
    environment: str = config("ENVIRONMENT", default="development")
    
    # Database
    database_url: str = config("DATABASE_URL", default="sqlite:///./ai_consultancy.db")
    
    # JWT Authentication
    secret_key: str = config("SECRET_KEY", default="your-secret-key-change-in-production")
    algorithm: str = config("ALGORITHM", default="HS256")
    access_token_expire_minutes: int = config("ACCESS_TOKEN_EXPIRE_MINUTES", default=30, cast=int)
    refresh_token_expire_days: int = config("REFRESH_TOKEN_EXPIRE_DAYS", default=7, cast=int)
    
    # Subscription Limits
    free_tier_monthly_tasks: int = config("FREE_TIER_MONTHLY_TASKS", default=10, cast=int)
    basic_tier_monthly_tasks: int = config("BASIC_TIER_MONTHLY_TASKS", default=100, cast=int)
    pro_tier_monthly_tasks: int = config("PRO_TIER_MONTHLY_TASKS", default=500, cast=int)
    enterprise_tier_monthly_tasks: int = config("ENTERPRISE_TIER_MONTHLY_TASKS", default=-1, cast=int)  # Unlimited
    
    # OpenAI
    openai_api_key: str = config("OPENAI_API_KEY", default="")
    
    # Social Media APIs
    twitter_api_key: str = config("TWITTER_API_KEY", default="")
    twitter_api_secret: str = config("TWITTER_API_SECRET", default="")
    twitter_access_token: str = config("TWITTER_ACCESS_TOKEN", default="")
    twitter_access_token_secret: str = config("TWITTER_ACCESS_TOKEN_SECRET", default="")
    twitter_bearer_token: str = config("TWITTER_BEARER_TOKEN", default="")
    telegram_bot_token: str = config("TELEGRAM_BOT_TOKEN", default="")
    
    # Image Generation
    stability_api_key: str = config("STABILITY_API_KEY", default="")
    huggingface_api_key: str = config("HUGGINGFACE_API_KEY", default="")
    
    # Redis & Celery
    redis_url: str = config("REDIS_URL", default="redis://localhost:6379/0")

    # CORS
    allowed_origins: Optional[str] = config("ALLOWED_ORIGINS", default="http://localhost:3000,http://127.0.0.1:3000")
    
    # Application
    debug: bool = config("DEBUG", default=True, cast=bool)
    environment: str = config("ENVIRONMENT", default="development")
    api_host: str = config("API_HOST", default="0.0.0.0")
    api_port: int = config("API_PORT", default=8000, cast=int)
    
    # File Upload
    upload_dir: str = config("UPLOAD_DIR", default="./uploads")
    max_file_size: int = config("MAX_FILE_SIZE", default=10485760, cast=int)  # 10MB
    
    # Subscription & Billing
    stripe_secret_key: str = config("STRIPE_SECRET_KEY", default="")
    stripe_publishable_key: str = config("STRIPE_PUBLISHABLE_KEY", default="")
    stripe_webhook_secret: str = config("STRIPE_WEBHOOK_SECRET", default="")
    
    # Email
    smtp_host: str = config("SMTP_HOST", default="smtp.gmail.com")
    smtp_port: int = config("SMTP_PORT", default=587, cast=int)
    smtp_user: str = config("SMTP_USER", default="")
    smtp_password: str = config("SMTP_PASSWORD", default="")
    
    # Admin User
    admin_username: str = config("ADMIN_USERNAME", default="admin")
    admin_email: str = config("ADMIN_EMAIL", default="admin@example.com")
    admin_password: str = config("ADMIN_PASSWORD", default="securepassword")

    class Config:
        env_file = ".env"
    
    def __post_init__(self):
        """Validate critical environment variables after initialization."""
        self._validate_environment()
    
    def _validate_environment(self):
        """Validate critical environment variables and log warnings for missing ones."""
        critical_vars = {
            'DATABASE_URL': self.database_url,
            'SECRET_KEY': self.secret_key,
            'REDIS_URL': self.redis_url
        }
        
        optional_vars = {
            'OPENAI_API_KEY': self.openai_api_key,
            'TWITTER_API_KEY': self.twitter_api_key,
            'TELEGRAM_BOT_TOKEN': self.telegram_bot_token,
            'STABILITY_API_KEY': self.stability_api_key,
            'STRIPE_SECRET_KEY': self.stripe_secret_key,
            'SMTP_USER': self.smtp_user
        }
        
        # Check critical variables
        for var_name, var_value in critical_vars.items():
            if not var_value or var_value in ['your-secret-key-change-in-production']:
                if self.environment == 'production':
                    logger.error(f"Critical environment variable {var_name} is not set or using default value")
                    raise ValueError(f"Critical environment variable {var_name} must be set in production")
                else:
                    logger.warning(f"Environment variable {var_name} is not set or using default value")
        
        # Check optional variables
        missing_optional = []
        for var_name, var_value in optional_vars.items():
            if not var_value:
                missing_optional.append(var_name)
        
        if missing_optional:
            logger.info(f"Optional environment variables not set: {', '.join(missing_optional)}")
            logger.info("Some features may be limited without these API keys")


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings
