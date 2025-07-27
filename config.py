"""Core configuration settings for the AI Consultancy Platform."""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    database_url: str = Field("sqlite:///./ai_consultancy.db", env="DATABASE_URL")
    
    # JWT Authentication
    secret_key: str = Field("your-secret-key-change-in-production", env="SECRET_KEY")
    algorithm: str = Field("HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(7, env="REFRESH_TOKEN_EXPIRE_DAYS")
    
    # Subscription Limits
    free_tier_monthly_tasks: int = Field(10, env="FREE_TIER_MONTHLY_TASKS")
    basic_tier_monthly_tasks: int = Field(100, env="BASIC_TIER_MONTHLY_TASKS")
    pro_tier_monthly_tasks: int = Field(500, env="PRO_TIER_MONTHLY_TASKS")
    enterprise_tier_monthly_tasks: int = Field(-1, env="ENTERPRISE_TIER_MONTHLY_TASKS")  # Unlimited
    
    # OpenAI
    openai_api_key: str = Field("", env="OPENAI_API_KEY")
    
    # Social Media APIs
    twitter_api_key: str = Field("", env="TWITTER_API_KEY")
    twitter_api_secret: str = Field("", env="TWITTER_API_SECRET")
    twitter_access_token: str = Field("", env="TWITTER_ACCESS_TOKEN")
    twitter_access_token_secret: str = Field("", env="TWITTER_ACCESS_TOKEN_SECRET")
    twitter_bearer_token: str = Field("", env="TWITTER_BEARER_TOKEN")
    telegram_bot_token: str = Field("", env="TELEGRAM_BOT_TOKEN")
    
    # Image Generation
    stability_api_key: str = Field("", env="STABILITY_API_KEY")
    huggingface_api_key: str = Field("", env="HUGGINGFACE_API_KEY")
    
    # Redis & Celery
    redis_url: str = Field("redis://localhost:6379/0", env="REDIS_URL")
    
    # Application
    debug: bool = Field(True, env="DEBUG")
    environment: str = Field("development", env="ENVIRONMENT")
    api_host: str = Field("0.0.0.0", env="API_HOST")
    api_port: int = Field(8000, env="API_PORT")
    allowed_origins: Optional[str] = Field("", env="ALLOWED_ORIGINS")
    
    # File Upload
    upload_dir: str = Field("./uploads", env="UPLOAD_DIR")
    max_file_size: int = Field(10485760, env="MAX_FILE_SIZE")  # 10MB
    
    # Subscription & Billing
    stripe_secret_key: str = Field("", env="STRIPE_SECRET_KEY")
    stripe_publishable_key: str = Field("", env="STRIPE_PUBLISHABLE_KEY")
    stripe_webhook_secret: str = Field("", env="STRIPE_WEBHOOK_SECRET")
    
    # Email
    smtp_host: str = Field("smtp.gmail.com", env="SMTP_HOST")
    smtp_port: int = Field(587, env="SMTP_PORT")
    smtp_user: str = Field("", env="SMTP_USER")
    smtp_password: str = Field("", env="SMTP_PASSWORD")
    
    class Config:
        env_file = ".env"
        extra = "ignore"


# Global settings instance
settings = Settings()
