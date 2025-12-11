"""Configuration management for Media Toolkit."""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Keys
    google_api_key: str = ""

    # Directories
    upload_dir: Path = Path("uploads")
    output_dir: Path = Path("outputs")

    # Server Configuration
    host: str = "127.0.0.1"
    port: int = 8000

    # File Handling
    max_upload_size_mb: int = 500
    temp_file_retention_hours: int = 1

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Global settings instance
settings = Settings()
