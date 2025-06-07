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
from .nodes_agents import story_creator_node, gamemaster_node, determine_next_agent

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


def compile_workflow(phase: str = "2") -> StateGraph:
    """
    Kompiliert den Workflow für Execution
    
    Args:
        phase: "1" für Foundation Chatbot, "2" für Agent-Based (default)
    
    Returns:
        Compiledworkflow ready for invocation
    """
    
    try:
        if phase == "1":
            workflow = create_chat_workflow()
            logger.info("Compiling Phase 1 workflow (Foundation Chatbot)")
        else:
            workflow = create_agent_workflow()
            logger.info("Compiling Phase 2 workflow (Agent-Based)")
        
        compiled = workflow.compile()
        
        logger.info("Workflow compiled successfully", phase=phase)
        return compiled
        
    except Exception as e:
        logger.error("Workflow compilation failed", error=str(e), phase=phase)
        raise


# Global Workflow Instances
_compiled_workflow_phase1 = None
_compiled_workflow_phase2 = None


def get_workflow(phase: str = "2") -> StateGraph:
    """
    Singleton Getter für kompilierten Workflow
    
    Args:
        phase: "1" für Foundation Chatbot, "2" für Agent-Based (default)
    
    Returns:
        Compiled workflow instance
    """
    global _compiled_workflow_phase1, _compiled_workflow_phase2
    
    if phase == "1":
        if _compiled_workflow_phase1 is None:
            _compiled_workflow_phase1 = compile_workflow("1")
        return _compiled_workflow_phase1
    else:
        if _compiled_workflow_phase2 is None:
            _compiled_workflow_phase2 = compile_workflow("2")
        return _compiled_workflow_phase2


def get_phase2_workflow() -> StateGraph:
    """
    Convenience function für Phase 2 Agent Workflow
    
    Returns:
        Compiled Phase 2 workflow
    """
    return get_workflow("2")


def reset_workflow_cache():
    """
    Reset workflow cache für Testing oder Reconfiguration
    """
    global _compiled_workflow_phase1, _compiled_workflow_phase2
    
    _compiled_workflow_phase1 = None
    _compiled_workflow_phase2 = None
    
    logger.info("Workflow cache reset")


# ===================================
# Phase 2: Agent-Based Workflow
# ===================================

def create_agent_workflow() -> StateGraph:
    """
    Erstellt den Agent-basierten Workflow für Phase 2
    
    Multi-Agent Flow mit automatischem Agent-Switching:
    1. Start → Story Creator (Standard Entry)
    2. Story Creator ⟷ Gamemaster (basierend auf Transition-Triggers)
    3. Conditional Routing mit determine_next_agent()
    
    Returns:
        StateGraph für Agent-Based Chat
    """
    
    # Create StateGraph mit ChatState
    workflow = StateGraph(ChatState)
    
    # Add Agent Nodes
    workflow.add_node("story_creator", story_creator_node)
    workflow.add_node("gamemaster", gamemaster_node)
    workflow.add_node("start", start_node)
    
    # Set Entry Point
    workflow.set_entry_point("start")
    
    logger.info("Creating agent workflow with Story Creator and Gamemaster")
    
    # Start → determine first agent
    workflow.add_conditional_edges(
        "start",
        determine_initial_agent,
        {
            "story_creator": "story_creator",
            "gamemaster": "gamemaster",
            "wait": END
        }
    )
    
    # Story Creator → Agent Router
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
    
    # Gamemaster → Agent Router
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
    
    logger.info("Agent workflow created with conditional routing")
    return workflow


def determine_initial_agent(state: ChatState) -> str:
    """
    Bestimmt den initialen Agent für neue Sessions
    
    Args:
        state: ChatState nach Start Node
        
    Returns:
        Initial agent node name
    """
    
    # Check if session is active
    if not state.active:
        logger.info("Session inactive at start, ending", session_id=state.session_id)
        return "end"
    
    # For new sessions, always start with Story Creator
    # (User kann später über Conversation Flow zum Gamemaster wechseln)
    if not state.current_agent:
        logger.info("New session, starting with Story Creator", session_id=state.session_id)
        return "story_creator"
    
    # If agent already set (e.g. from session restore), continue with that agent
    current_agent = state.current_agent
    logger.info("Existing session, continuing with current agent", 
               session_id=state.session_id,
               current_agent=current_agent)
    
    return current_agent if current_agent in ["story_creator", "gamemaster"] else "story_creator" 