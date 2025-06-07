"""
TextRPG Backend Configuration
Pydantic Settings für sichere Environment Variable-Verwaltung
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional
import os
from pathlib import Path


class Settings(BaseSettings):
    """
    Application Settings mit Type Safety und Validation
    Lädt Environment Variables aus .env im Root-Verzeichnis
    """
    
    # OpenRouter API Configuration  
    openrouter_api_key: str = Field(
        ..., 
        description="OpenRouter API Key für LLM-Integration"
    )
    
    # LLM Model Configuration
    llm_default: str = Field(
        default="google/gemini-2.5-flash-preview-05-20",
        alias="LLM_DEFAULT",
        description="Standard LLM Model für Phase 1"
    )
    
    llm_creator: str = Field(
        default="google/gemini-2.0-flash-exp", 
        description="Story Creator Agent Model"
    )
    
    llm_gamemaster: str = Field(
        default="google/gemini-2.5-flash-preview-05-20",
        description="Gamemaster Agent Model"
    )
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", description="FastAPI Host")
    api_port: int = Field(default=8000, description="FastAPI Port")
    
    # Development Configuration
    debug: bool = Field(default=True, description="Debug Mode")
    reload: bool = Field(default=True, description="Auto-reload in Development")
    
    # CORS Configuration
    cors_origins: list[str] = Field(
        default=["http://localhost:5173", "http://127.0.0.1:5173"],
        description="Erlaubte CORS Origins für Frontend"
    )
    
    # Logging Configuration
    log_level: str = Field(default="info", description="Logging Level")
    
    # Session Configuration
    default_session_timeout: int = Field(
        default=3600, 
        description="Standard Session Timeout in Sekunden"
    )

    model_config = SettingsConfigDict(
        # .env liegt im backend directory
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # Ignoriere unbekannte Environment Variables
    )


# Global Settings Instance
def get_settings() -> Settings:
    """
    Singleton Pattern für Settings
    Lazy Loading mit Caching
    """
    if not hasattr(get_settings, "_settings"):
        get_settings._settings = Settings()
    return get_settings._settings


# Convenience Export
settings = get_settings() 