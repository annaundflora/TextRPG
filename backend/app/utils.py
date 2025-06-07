"""
TextRPG Backend Utilities
Helper-Funktionen für Configuration und Environment-Setup
"""

import os
from pathlib import Path
from typing import Dict, Any
import structlog

from .config import settings, Settings

logger = structlog.get_logger()


def validate_configuration() -> Dict[str, Any]:
    """
    Validiert die aktuelle Configuration und gibt Details zurück
    
    Returns:
        Dict mit Validation-Ergebnissen und Config-Details
    """
    validation_result = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "config_details": {}
    }
    
    try:
        # Test Settings Loading
        config = Settings()
        
        # Validiere kritische Felder
        if not config.openrouter_api_key:
            validation_result["errors"].append("OPENROUTER_API_KEY ist leer oder nicht gesetzt")
            validation_result["valid"] = False
        elif config.openrouter_api_key == "your_key_here":
            validation_result["warnings"].append("OPENROUTER_API_KEY scheint noch ein Platzhalter zu sein")
            
        # Config Details sammeln (ohne sensitive Daten)            
        validation_result["config_details"] = {
            "llm_default": config.llm_default,
            "llm_creator": config.llm_creator, 
            "llm_gamemaster": config.llm_gamemaster,
            "api_host": config.api_host,
            "api_port": config.api_port,
            "debug": config.debug,
            "log_level": config.log_level,
            "cors_origins": config.cors_origins,
            "env_file_path": str(Path(__file__).parent.parent / ".env")
        }
        
        logger.info("Configuration validation completed", 
                   valid=validation_result["valid"],
                   errors_count=len(validation_result["errors"]),
                   warnings_count=len(validation_result["warnings"]))
        
    except Exception as e:
        validation_result["valid"] = False
        validation_result["errors"].append(f"Configuration loading failed: {str(e)}")
        logger.error("Configuration validation failed", error=str(e))
    
    return validation_result


def check_environment() -> Dict[str, Any]:
    """
    Überprüft die Environment-Setup für Development
    
    Returns:
        Dict mit Environment-Status
    """
    env_check = {
        "ready": True,
        "issues": [],
        "details": {}
    }
    
    # Überprüfe .env Datei im backend directory
    env_file_path = Path(__file__).parent.parent / ".env"
    env_check["details"]["env_file_path"] = str(env_file_path)
    env_check["details"]["env_file_exists"] = env_file_path.exists()
    
    if not env_file_path.exists():
        env_check["ready"] = False
        env_check["issues"].append(f".env Datei nicht gefunden: {env_file_path}")
    
    # Überprüfe wichtige Environment Variables
    required_vars = ["OPENROUTER_API_KEY"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        env_check["ready"] = False
        env_check["issues"].append(f"Fehlende Environment Variables: {', '.join(missing_vars)}")
    
    env_check["details"]["required_vars"] = required_vars
    env_check["details"]["missing_vars"] = missing_vars
    
    return env_check


def get_startup_info() -> Dict[str, Any]:
    """
    Sammelt alle Startup-Informationen für Logging
    
    Returns:
        Dict mit vollständigen Startup-Details
    """
    config_validation = validate_configuration()
    env_check = check_environment()
    
    return {
        "phase": "1 - Foundation Chatbot",
        "version": "1.0.0-phase1",
        "configuration": config_validation,
        "environment": env_check,
        "ready_for_startup": config_validation["valid"] and env_check["ready"]
    } 