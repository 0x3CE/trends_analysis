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
    
    # Test mode detection (automatiquement détecté)
    testing: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Détection automatique du mode test
        self.testing = (
            os.getenv("TESTING", "").lower() == "true" or
            "pytest" in os.getenv("_", "") or
            "pytest" in str(os.getenv("PYTEST_CURRENT_TEST", ""))
        )
    
    def is_sqlite(self) -> bool:
        """Vérifie si on utilise SQLite."""
        return self.database_url.startswith("sqlite")
    
    def is_memory_db(self) -> bool:
        """Vérifie si on utilise une base en mémoire (pour les tests)."""
        return ":memory:" in self.database_url


settings = Settings()