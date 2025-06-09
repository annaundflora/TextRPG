# Agents Package - VEREINFACHTE VERSION

from .setup_agent import SetupAgent
from .gameplay_agent import GameplayAgent
from .prompt_loader import load_prompt_from_file, extract_system_prompt

__all__ = [
    "SetupAgent",
    "GameplayAgent", 
    "load_prompt_from_file",
    "extract_system_prompt"
] 