# app/config.py
"""Configuration management for the Twitter/X collector application."""
import os
from typing import Optional
from pydantic import BaseSettings

class Settings(BaseSettings):
    """Application settings with validation and environment variable support."""
    
    # Database configuration
    database_url: str = "sqlite:///./tweets.db"
    
    # Twitter/X API configuration
    x_api_base: str = "https://api.x.com/2"
    bearer_token: Optional[str] = None
    
    # Application configuration
    app_name: str = "Twitter/X Collector"
    debug: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()