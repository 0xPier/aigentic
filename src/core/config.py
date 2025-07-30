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
    
    # JWT Configuration  
    algorithm: str = config("ALGORITHM", default="HS256")
    access_token_expire_minutes: int = config("ACCESS_TOKEN_EXPIRE_MINUTES", default=1440, cast=int)
    refresh_token_expire_days: int = config("REFRESH_TOKEN_EXPIRE_DAYS", default=7, cast=int)
    
    # Redis Configuration
    redis_url: str = config("REDIS_URL", default="redis://localhost:6379/0")
    
    # Celery Configuration
    celery_broker_url: str = config("CELERY_BROKER_URL", default="redis://localhost:6379/0")
    celery_result_backend: str = config("CELERY_RESULT_BACKEND", default="redis://localhost:6379/0")
    
    # Storage Configuration
    upload_dir: str = config("UPLOAD_DIR", default="./uploads")
    max_upload_size: int = config("MAX_UPLOAD_SIZE", default=10485760, cast=int)  # 10MB
    
    # Logging Configuration
    log_level: str = config("LOG_LEVEL", default="INFO")
    log_file: str = config("LOG_FILE", default="./logs/app.log")
    
    # CORS
    allowed_origins: Optional[str] = config("ALLOWED_ORIGINS", default="http://localhost:3000,http://127.0.0.1:3000")
    
    # Application
    debug: bool = config("DEBUG", default=True, cast=bool)
    api_host: str = config("API_HOST", default="0.0.0.0")
    api_port: int = config("API_PORT", default=8000, cast=int)
    
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
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._validate_environment()
    
    def _validate_environment(self):
        """Validate environment configuration."""
        # Check if running in production
        if self.environment == "production":
            # Warn about missing production configurations
            missing_configs = []
            
            if not self.openai_api_key and self.llm_provider == "openai":
                missing_configs.append("OPENAI_API_KEY")
            
            if self.secret_key == "your-secret-key-change-in-production":
                missing_configs.append("SECRET_KEY (using default)")
            
            if missing_configs:
                logger.warning(f"Production environment detected but missing configurations: {', '.join(missing_configs)}")
        
        # Validate database URL
        if not self.database_url:
            logger.error("DATABASE_URL is required")
            raise ValueError("DATABASE_URL configuration is required")
        
        # Log configuration summary
        logger.info(f"Environment: {self.environment}")
        logger.info(f"Database: {self.database_url}")
        logger.info(f"LLM Provider: {self.llm_provider}")
        
        if self.environment == "development":
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
