import os
from typing import List
from pydantic import BaseSettings, AnyHttpUrl
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """Application settings."""
    
    # API settings
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", 8001))  # Different from calendar service
    
    # Application settings
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    
    # CORS settings
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",  # Frontend
        "http://localhost:8000",  # Calendar microservice
    ]
    
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./sleep_data.db")
    
    # Calendar service integration
    CALENDAR_SERVICE_URL: str = os.getenv("CALENDAR_SERVICE_URL", "http://localhost:8000")
    
    # Storage settings
    STORAGE_TYPE: str = os.getenv("STORAGE_TYPE", "file")  # Options: file, database
    FILE_STORAGE_PATH: str = os.getenv("FILE_STORAGE_PATH", "./data")
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    VERSION: str = "0.1.0"
    SHOW_DOCS: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Create an instance of the settings
settings = Settings()