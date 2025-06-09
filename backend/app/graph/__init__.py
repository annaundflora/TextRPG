"""
TextRPG Graph Module - VEREINFACHTE VERSION
LangGraph Workflow für Setup und Gameplay Agents
"""

from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command

from .workflow import (
    create_text_rpg_workflow,
    compile_workflow,
    get_workflow,
    reset_workflow_cache
)

from .nodes_agents import (
    setup_agent_node,
    gameplay_agent_node,
    get_setup_agent,
    get_gameplay_agent
)

from .session_manager import (
    SessionManager,
    get_session_manager
)

from ..models.state import ChatState

import logging

logger = logging.getLogger(__name__)


def should_continue_to_gameplay(state: Dict[str, Any]) -> Literal["gameplay_agent", END]:
    """
    Router function für Setup Agent Output
    Prüft ob Command für Transition zu Gameplay Agent vorliegt
    """
    # Wenn setup_agent_node ein Command zurückgibt, wird automatisch zu gameplay_agent geleitet
    # Sonst bleibt es beim setup_agent
    logger.info("Routing decision: staying in setup for more input")
    return END  # Default: Ende, es sei denn Command sagt etwas anderes


def create_text_rpg_workflow() -> StateGraph:
    """
    Erstellt den LangGraph Workflow für TextRPG
    
    Returns:
        StateGraph: Configured workflow
    """
    # Create StateGraph
    workflow = StateGraph(Dict[str, Any])
    
    # Add nodes
    workflow.add_node("setup_agent", setup_agent_node)
    workflow.add_node("gameplay_agent", gameplay_agent_node)
    
    # Entry point: Immer Setup Agent
    workflow.add_edge(START, "setup_agent")
    
    # Conditional edges für Setup Agent
    # WICHTIG: LangGraph behandelt Command-Returns automatisch!
    workflow.add_conditional_edges(
        "setup_agent",
        should_continue_to_gameplay,
        {
            "gameplay_agent": "gameplay_agent",
            END: END
        }
    )
    
    # Gameplay Agent endet normalerweise (kann erweitert werden)
    workflow.add_edge("gameplay_agent", END)
    
    logger.info("TextRPG workflow created with Command support")
    
    return workflow


def create_agent_workflow() -> StateGraph:
    """
    Alias für create_text_rpg_workflow (Legacy-Kompatibilität)
    """
    return create_text_rpg_workflow()

__all__ = [
    # Workflow Management
    "create_text_rpg_workflow",
    "create_agent_workflow", 
    "compile_workflow",
    "get_workflow",
    "reset_workflow_cache",
    
    # Node Functions
    "setup_agent_node",
    "gameplay_agent_node",
    
    # Agent Getters
    "get_setup_agent",
    "get_gameplay_agent",
    
    # Router Functions
    "should_continue_to_gameplay",
    
    # Session Management
    "SessionManager",
    "get_session_manager"
] 