"""
Application configuration - loads environment variables
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # API Keys
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    google_api_key: Optional[str] = None

    # App Settings
    debug: bool = True
    log_level: str = "INFO"

    # Memory settings
    memory_dir: str = "memory"

    # Vector Database settings
    use_vector_db: bool = True
    vector_db_dir: str = "vector_db"
    embedding_model: str = "all-MiniLM-L6-v2"

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_api_key(provider: str) -> Optional[str]:
    """Get API key for a specific provider"""
    key_map = {
        "anthropic": settings.anthropic_api_key,
        "openai": settings.openai_api_key,
        "google": settings.google_api_key,
        "gemini": settings.google_api_key,
    }
    return key_map.get(provider.lower())