"""
TextRPG LangGraph Workflow
Workflow-Definition für Phase 1 - Foundation Chatbot
"""

from typing import Dict, Any, Annotated
from langgraph.graph import StateGraph
try:
    from langgraph.graph import END
except ImportError:
    # Fallback für unterschiedliche LangGraph Versionen
    END = "__end__"
from langgraph.graph.message import add_messages
import structlog

from ..models import ChatState
from .nodes import generic_chat_node, start_node, should_continue

logger = structlog.get_logger()


def create_chat_workflow() -> StateGraph:
    """
    Erstellt den LangGraph Workflow für Phase 1
    
    Einfacher Chat-Flow ohne Agent-Switching:
    1. Start Node → Initialisierung
    2. Chat Node → Message Processing 
    3. Continue/End basierend auf Session-Status
    
    Returns:
        Kompilierter StateGraph
    """
    
    # Define State Schema
    # In LangGraph verwenden wir TypedDict für State Definition
    class GraphState(ChatState):
        """Extended State für LangGraph mit Message Handling"""
        pass
    
    # Create StateGraph
    workflow = StateGraph(ChatState)
    
    # Add Nodes
    workflow.add_node("start", start_node)
    workflow.add_node("chat", generic_chat_node)
    
    # Set Entry Point
    workflow.set_entry_point("start")
    
    # Add Edges
    workflow.add_edge("start", "chat")
    
    # Add Conditional Edge für Flow Control
    workflow.add_conditional_edges(
        "chat",
        should_continue,
        {
            "chat": "chat",  # Continue chatting
            "wait": END,     # Wait for user input
            "end": END       # End session
        }
    )
    
    logger.info("Chat workflow created successfully")
    return workflow


def compile_workflow() -> StateGraph:
    """
    Kompiliert den Workflow für Execution
    
    Returns:
        Compiledworkflow ready for invocation
    """
    
    try:
        workflow = create_chat_workflow()
        compiled = workflow.compile()
        
        logger.info("Workflow compiled successfully")
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


# Phase 2 Vorbereitung - Agent Workflow (auskommentiert)
"""
def create_agent_workflow() -> StateGraph:
    # Phase 2: Multi-Agent Workflow mit Story Creator und Gamemaster
    
    workflow = StateGraph(ChatState)
    
    # Add Agent Nodes
    workflow.add_node("story_creator", story_creator_node)
    workflow.add_node("gamemaster", gamemaster_node)
    workflow.add_node("start", start_node)
    
    # Set Entry Point
    workflow.set_entry_point("start")
    
    # Add Agent Routing
    workflow.add_conditional_edges(
        "start",
        determine_initial_agent,
        {
            "story_creator": "story_creator",
            "gamemaster": "gamemaster"
        }
    )
    
    # Story Creator Transitions
    workflow.add_conditional_edges(
        "story_creator",
        determine_next_agent,
        {
            "story_creator": "story_creator",
            "gamemaster": "gamemaster",
            "end": END
        }
    )
    
    # Gamemaster Transitions
    workflow.add_conditional_edges(
        "gamemaster", 
        determine_next_agent,
        {
            "story_creator": "story_creator",
            "gamemaster": "gamemaster", 
            "end": END
        }
    )
    
    return workflow
""" 