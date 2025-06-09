"""
TextRPG LangGraph Workflow - VEREINFACHTE VERSION
Workflow für Setup und Gameplay Agents mit Command Pattern
"""

from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
import logging

from .nodes_agents import setup_agent_node, gameplay_agent_node

logger = logging.getLogger(__name__)


def should_continue_to_gameplay(state: Dict[str, Any]) -> Literal["gameplay_agent", END]:
    """
    Router function für Setup Agent Output
    LangGraph behandelt Commands automatisch, aber wir brauchen diese Funktion noch für conditional edges
    """
    # LangGraph übernimmt Command-Routing automatisch
    logger.info("Default routing: ending workflow after setup")
    return END


def create_text_rpg_workflow() -> StateGraph:
    """
    Erstellt vereinfachten Workflow für TextRPG mit Command-Unterstützung
    
    Flow: Start → Setup Agent → (Command) → Gameplay Agent → End
    
    Returns:
        StateGraph mit command-based routing
    """
    
    # Create StateGraph (wird dict-based state nutzen)
    workflow = StateGraph(Dict[str, Any])
    
    # Add Nodes mit korrekten Namen
    workflow.add_node("setup_agent", setup_agent_node)
    workflow.add_node("gameplay_agent", gameplay_agent_node)
    
    # Entry point: Immer Setup Agent
    workflow.add_edge(START, "setup_agent")
    
    # Conditional edges für Setup Agent
    # LangGraph behandelt Command-Returns automatisch!
    workflow.add_conditional_edges(
        "setup_agent",
        should_continue_to_gameplay,
        {
            "gameplay_agent": "gameplay_agent",
            END: END
        }
    )
    
    # Gameplay Agent endet normalerweise
    workflow.add_edge("gameplay_agent", END)
    
    logger.info("TextRPG workflow created with Command support and correct node names")
    
    return workflow


def compile_workflow() -> StateGraph:
    """
    Kompiliert den Workflow
    
    Returns:
        Compiled workflow
    """
    
    try:
        workflow = create_text_rpg_workflow()
        compiled = workflow.compile()
        logger.info("TextRPG workflow compiled successfully")
        return compiled
        
    except Exception as e:
        logger.error("Workflow compilation failed", error=str(e))
        raise


# Singleton Pattern
_compiled_workflow = None


def get_workflow() -> StateGraph:
    """
    Singleton Getter für kompilierten Workflow
    
    Returns:
        Compiled workflow instance
    """
    global _compiled_workflow
    
    if _compiled_workflow is None:
        _compiled_workflow = compile_workflow()
    
    return _compiled_workflow


def reset_workflow_cache():
    """
    Reset workflow cache für Testing
    """
    global _compiled_workflow
    _compiled_workflow = None 