"""
Configuration management for Mahoraga Triage Engine
Handles environment variables and system settings
"""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database
    database_url: str = Field(default="sqlite:///./mahoraga.db", env="DATABASE_URL")
    
    # API Keys
    github_token: Optional[str] = Field(default=None, env="GITHUB_TOKEN")
    github_webhook_secret: Optional[str] = Field(default=None, env="GITHUB_WEBHOOK_SECRET")
    slack_bot_token: Optional[str] = Field(default=None, env="SLACK_BOT_TOKEN")
    gemini_api_key: Optional[str] = Field(default=None, env="GEMINI_API_KEY")
    
    # System Configuration
    confidence_threshold: float = Field(default=60.0, env="CONFIDENCE_THRESHOLD")
    draft_pr_enabled: bool = Field(default=True, env="DRAFT_PR_ENABLED")
    duplicate_detection_window_minutes: int = Field(default=10, env="DUPLICATE_DETECTION_WINDOW_MINUTES")
    
    # Performance Settings
    webhook_timeout_seconds: int = Field(default=30, env="WEBHOOK_TIMEOUT_SECONDS")
    git_blame_timeout_seconds: int = Field(default=5, env="GIT_BLAME_TIMEOUT_SECONDS")
    ai_analysis_timeout_seconds: int = Field(default=30, env="AI_ANALYSIS_TIMEOUT_SECONDS")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings"""
    return settings


def validate_required_env_vars() -> dict[str, bool]:
    """
    Validate that required environment variables are set
    Returns dict mapping env var names to whether they're set
    """
    required_vars = {
        "GITHUB_TOKEN": settings.github_token is not None,
        "GITHUB_WEBHOOK_SECRET": settings.github_webhook_secret is not None,
        "SLACK_BOT_TOKEN": settings.slack_bot_token is not None,
        "GEMINI_API_KEY": settings.gemini_api_key is not None,
    }
    return required_vars


def is_system_configured() -> bool:
    """Check if all required environment variables are configured"""
    validation_results = validate_required_env_vars()
    return all(validation_results.values())