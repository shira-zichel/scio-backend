"""
Configuration management for SCiO Backend.
Uses Pydantic Settings to load from environment variables and .env file.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Data settings
    data_dir: str = "data"
    
    # App settings
    app_name: str = "SCiO Backend API"
    app_description: str = "API for retrieving Scan Analysis Reports"
    app_version: str = "1.0.0"
    debug: bool = False
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Single instance to import everywhere
settings = Settings()

