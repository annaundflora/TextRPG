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
    
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        description="OpenRouter API Base URL"
    )
    
    # LLM Model Configuration
    llm_default: str = Field(
        default="google/gemini-2.5-pro-preview",
        alias="LLM_DEFAULT",
        description="Standard LLM Model für Phase 1"
    )
    
    llm_creator: str = Field(
        default="google/gemini-2.5-pro-preview", 
        alias="LLM_CREATOR",
        description="Story Creator Agent Model"
    )
    
    llm_gamemaster: str = Field(
        default="google/gemini-2.5-pro-preview",
        alias="LLM_GAMEMASTER",
        description="Gamemaster Agent Model"
    )
    
    # LangSmith Configuration
    langsmith_tracing: bool = Field(
        default=False,
        alias="LANGSMITH_TRACING",
        description="Enable LangSmith Tracing"
    )
    
    langsmith_api_key: Optional[str] = Field(
        default=None,
        alias="LANGSMITH_API_KEY", 
        description="LangSmith API Key"
    )
    
    langsmith_endpoint: str = Field(
        default="https://eu.api.smith.langchain.com",
        alias="LANGSMITH_ENDPOINT",
        description="LangSmith API Endpoint"
    )
    
    langsmith_project: str = Field(
        default="TextRPG",
        alias="LANGSMITH_PROJECT",
        description="LangSmith Project Name"
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
        # .env liegt im root directory
        env_file="../.env",
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