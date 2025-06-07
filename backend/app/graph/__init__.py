"""
TextRPG Graph Package
LangGraph Workflows & Nodes für Chat Processing
"""

from .workflow import (
    create_chat_workflow,
    create_agent_workflow,
    compile_workflow,
    get_workflow,
    get_phase2_workflow,
    reset_workflow_cache,
    determine_initial_agent
)

from .nodes import (
    generic_chat_node,
    start_node,
    should_continue
)

from .nodes_agents import (
    story_creator_node,
    gamemaster_node,
    determine_next_agent
)

from .session_manager import (
    SessionManager,
    get_session_manager
)

__all__ = [
    # Workflow
    "create_chat_workflow",
    "create_agent_workflow",
    "compile_workflow", 
    "get_workflow",
    "get_phase2_workflow",
    "reset_workflow_cache",
    "determine_initial_agent",
    
    # Nodes
    "generic_chat_node",
    "start_node",
    "should_continue",
    
    # Agent Nodes (Phase 2)
    "story_creator_node",
    "gamemaster_node", 
    "determine_next_agent",
    
    # Session Management
    "SessionManager",
    "get_session_manager"
] 