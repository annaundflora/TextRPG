"""
TextRPG LangGraph Workflow - Simplified for MVP
Vereinfachte Workflow-Definition für Agent-basiertes TextRPG
"""

from langgraph.graph import StateGraph
try:
    from langgraph.graph import END
except ImportError:
    # Fallback für unterschiedliche LangGraph Versionen
    END = "__end__"
import structlog

from ..models import ChatState
from .nodes_agents import story_creator_node, gamemaster_node, determine_next_agent

logger = structlog.get_logger()


def create_agent_workflow() -> StateGraph:
    """
    Erstellt den vereinfachten Agent-Workflow für MVP
    
    Einfacher Flow:
    Story Creator ⟷ Gamemaster basierend auf Transition-Markern
    
    Returns:
        StateGraph für Agent-Based Chat
    """
    
    # Create StateGraph mit ChatState
    workflow = StateGraph(ChatState)
    
    # Add Agent Nodes
    workflow.add_node("story_creator", story_creator_node)
    workflow.add_node("gamemaster", gamemaster_node)
    
    # Set Entry Point - immer Story Creator
    workflow.set_entry_point("story_creator")
    
    # Simple Conditional Routing für beide Agents
    workflow.add_conditional_edges(
        "story_creator",
        determine_next_agent,
        {
            "story_creator": "story_creator",
            "gamemaster": "gamemaster",
            "wait": END,
            "end": END
        }
    )
    
    workflow.add_conditional_edges(
        "gamemaster", 
        determine_next_agent,
        {
            "story_creator": "story_creator",
            "gamemaster": "gamemaster",
            "wait": END,
            "end": END
        }
    )
    
    return workflow


def compile_workflow() -> StateGraph:
    """
    Kompiliert den Workflow für Execution
    
    Returns:
        Compiled workflow ready for invocation
    """
    
    try:
        workflow = create_agent_workflow()
        compiled = workflow.compile()
        return compiled
        
    except Exception as e:
        logger.error("Workflow compilation failed", error=str(e))
        raise


# Global Workflow Instance
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
    Reset workflow cache für Testing oder Reconfiguration
    """
    global _compiled_workflow
    _compiled_workflow = None 