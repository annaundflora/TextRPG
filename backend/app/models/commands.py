"""
TextRPG Command Pattern Types - VEREINFACHTE VERSION
Einfache Command-Struktur für Agent Transitions
"""

from typing import Literal, Union, Dict, Any, Optional


# Command Types für Agent Transitions
CommandType = Literal[
    "setup_agent",      # Go to Setup Agent
    "gameplay_agent",   # Go to Gameplay Agent  
    "end"               # End the session
]

# Vereinfachter Command Return Type
AgentCommand = Dict[str, Any]


def create_goto_command(target: str, **updates) -> AgentCommand:
    """
    Erstellt einfachen goto Command
    
    Args:
        target: Ziel-Agent oder "end"
        **updates: State-Updates
        
    Returns:
        Command dict
    """
    command = {"goto": target}
    
    if updates:
        command["update"] = updates
    
    return command


def create_update_command(**updates) -> AgentCommand:
    """
    Erstellt einfachen update Command
    
    Args:
        **updates: State-Updates
        
    Returns:
        Command dict
    """
    return {"update": updates} 