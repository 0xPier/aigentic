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
    database_url: str = config("DATABASE_URL", default="mongodb://localhost:27017/agentic_platform")
    
    # Security
    secret_key: str = config("SECRET_KEY", default="your-secret-key-change-in-production")
    
    # Subscription Limits
    free_tier_monthly_tasks: int = config("FREE_TIER_MONTHLY_TASKS", default=10, cast=int)
    basic_tier_monthly_tasks: int = config("BASIC_TIER_MONTHLY_TASKS", default=100, cast=int)
    pro_tier_monthly_tasks: int = config("PRO_TIER_MONTHLY_TASKS", default=500, cast=int)
    enterprise_tier_monthly_tasks: int = config("ENTERPRISE_TIER_MONTHLY_TASKS", default=-1, cast=int)  # Unlimited
    
    # LLM Configuration
    llm_provider: str = config("LLM_PROVIDER", default="openai")  # openai, ollama, anthropic, etc.
    openai_api_key: str = config("OPENAI_API_KEY", default="")
    openai_api_base: str = config("OPENAI_API_BASE", default="https://api.openai.com/v1")
    ollama_base_url: str = config("OLLAMA_BASE_URL", default="http://localhost:11434")
    ollama_model: str = config("OLLAMA_MODEL", default="llama2")
    anthropic_api_key: str = config("ANTHROPIC_API_KEY", default="")
    
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
    
    

    class Config:
        env_file = ".env"
        extra = "allow"  # Allow extra fields from environment
    
    def __post_init__(self):
        """Validate critical environment variables after initialization."""
        self._validate_environment()
    
    def _validate_environment(self):
        """Validate critical environment variables and log warnings for missing ones."""
        critical_vars = {
            'DATABASE_URL': self.database_url,
            'REDIS_URL': self.redis_url
        }
        
        # For self-hosted setup, SECRET_KEY is less critical - generate a default if needed
        if not self.secret_key or self.secret_key in ['your-secret-key-change-in-production']:
            logger.info("Using default secret key for self-hosted setup")
        
        optional_vars = {
            'OPENAI_API_KEY': self.openai_api_key,
            'TWITTER_API_KEY': self.twitter_api_key,
            'TELEGRAM_BOT_TOKEN': self.telegram_bot_token,
            'STABILITY_API_KEY': self.stability_api_key,
            'STRIPE_SECRET_KEY': self.stripe_secret_key,
            'SMTP_USER': self.smtp_user
        }
        
        # Check critical variables (removed SECRET_KEY for self-hosted)
        for var_name, var_value in critical_vars.items():
            if not var_value:
                logger.warning(f"Environment variable {var_name} is not set - some features may not work")
        
        # Check optional variables
        missing_optional = []
        for var_name, var_value in optional_vars.items():
            if not var_value:
                missing_optional.append(var_name)
        
        # Relaxed validation for self-hosted setup
        if self.llm_provider == "openai" and not self.openai_api_key:
            logger.warning("OPENAI_API_KEY is not set - OpenAI features will not work.")

        if missing_optional:
            logger.info(f"Optional environment variables not set: {', '.join(missing_optional)}")
            logger.info("Some features may be limited without these API keys - this is normal for self-hosted setups")
    
    def get_llm_config(self):
        """Get LLM configuration based on provider."""
        if self.llm_provider == "openai":
            return {
                "provider": "openai",
                "api_key": self.openai_api_key,
                "api_base": self.openai_api_base,
                "model": "gpt-3.5-turbo"
            }
        elif self.llm_provider == "ollama":
            return {
                "provider": "ollama",
                "base_url": self.ollama_base_url,
                "model": self.ollama_model
            }
        elif self.llm_provider == "anthropic":
            return {
                "provider": "anthropic",
                "api_key": self.anthropic_api_key,
                "model": "claude-3-sonnet-20240229"
            }
        else:
            return {
                "provider": "openai",
                "api_key": self.openai_api_key,
                "api_base": self.openai_api_base,
                "model": "gpt-3.5-turbo"
            }


# Global settings instance
app_config = Settings()


def get_app_config() -> Settings:
    """Get application settings."""
    return app_config
