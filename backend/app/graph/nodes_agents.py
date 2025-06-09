"""
TextRPG Agent Nodes - Simplified for MVP
Vereinfachte Agent-Node-Funktionen für LangGraph Workflow
"""

from typing import Dict, Any
import structlog
from datetime import datetime

from ..models import ChatState, ChatMessage, create_human_message, create_ai_message, AgentType
from ..agents import StoryCreatorAgent, GamemasterAgent
from ..config import settings
from langchain_openai import ChatOpenAI

logger = structlog.get_logger()

# Transition Markers
GAMEMASTER_MARKER = "--- HANDLUNGSOPTIONEN ---"
STORY_CREATOR_MARKER = "--- STORY CREATOR ÜBERGANG ---"


async def generic_agent_node(state: ChatState, agent_type: AgentType) -> Dict[str, Any]:
    """
    Generic Agent Node für beide Agents - Eliminiert Code-Duplikation
    
    Args:
        state: Current ChatState
        agent_type: "story_creator" oder "gamemaster"
        
    Returns:
        Updated state dict
    """
    
    try:
        # Set current agent
        if state.current_agent != agent_type:
            state.switch_agent(agent_type)
        
        # Validate state
        if not state.last_user_message:
            return {"processing": False}
        
        # Add user message if not already in conversation
        if not state.messages or state.messages[-1].type != "human":
            user_message = create_human_message(state.last_user_message)
            state.add_message(user_message)
        
        # Initialize LLM and Agent
        llm_model = settings.llm_creator if agent_type == "story_creator" else settings.llm_gamemaster
        llm = ChatOpenAI(
            base_url=settings.openrouter_base_url,
            api_key=settings.openrouter_api_key,
            model=llm_model
        )
        
        # Create appropriate agent
        if agent_type == "story_creator":
            agent = StoryCreatorAgent(llm)
        else:
            agent = GamemasterAgent(llm)
        
        # Get recent messages for context
        recent_messages = state.get_recent_messages(limit=10)
        
        # Generate response - simplified agent context
        agent_context = {
            "current_agent": state.current_agent,
            "message_count": len(state.messages)
        }
        
        response_text, should_transition, transition_trigger = agent.process_message(
            recent_messages, agent_context
        )
        
        # Create AI response
        ai_response = create_ai_message(
            response_text,
            metadata={
                "agent": agent_type,
                "model": llm_model,
                "should_transition": should_transition
            }
        )
        
        # Add to conversation
        state.add_message(ai_response)
        
        # DON'T clear user message here - let determine_next_agent decide
        # state.last_user_message = None  # REMOVED - this was causing the problem!
        
        # Return updated state with all fields
        return {
            "session_id": state.session_id,
            "messages": state.messages,
            "processing": False,
            "last_user_message": state.last_user_message,  # Keep it for now
            "last_updated": datetime.utcnow(),
            "current_agent": state.current_agent,
            "active": state.active,
            "created_at": state.created_at
        }
        
    except Exception as e:
        # Simple error response
        error_message = create_ai_message(
            f"Entschuldigung, es gab ein Problem. Bitte versuche es erneut.",
            metadata={"error": True, "agent": agent_type}
        )
        
        state.add_message(error_message)
        
        return {
            "messages": state.messages,
            "processing": False,
            "last_updated": datetime.utcnow(),
            "current_agent": state.current_agent
        }


async def story_creator_node(state: ChatState) -> Dict[str, Any]:
    """
    Story Creator Node - Wrapper um generic_agent_node
    """
    return await generic_agent_node(state, "story_creator")


async def gamemaster_node(state: ChatState) -> Dict[str, Any]:
    """
    Gamemaster Node - Wrapper um generic_agent_node
    """
    return await generic_agent_node(state, "gamemaster")


def should_transition_to_gamemaster(state: ChatState) -> bool:
    """
    Check if last AI message contains gamemaster transition marker
    AND was sent by the story creator (prevents loops)
    """
    if not state.messages:
        return False
    
    last_message = state.messages[-1]
    
    # Only transition if:
    # 1. Message is from AI
    # 2. Contains the gamemaster marker
    # 3. Was sent by the story_creator (not gamemaster itself!)
    if (last_message.type == "ai" and 
        GAMEMASTER_MARKER in last_message.content and 
        last_message.metadata.get("agent") == "story_creator"):
        logger.info("Transition to gamemaster triggered by story_creator")
        return True
    
    return False


def should_transition_to_story_creator(state: ChatState) -> bool:
    """
    Check if last AI message contains story creator transition marker
    AND was sent by the gamemaster (prevents loops)
    """
    if not state.messages:
        return False
    
    last_message = state.messages[-1]
    
    # Only transition if:
    # 1. Message is from AI
    # 2. Contains the story creator marker  
    # 3. Was sent by the gamemaster (not story_creator itself!)
    if (last_message.type == "ai" and 
        STORY_CREATOR_MARKER in last_message.content and 
        last_message.metadata.get("agent") == "gamemaster"):
        logger.info("Transition to story_creator triggered by gamemaster")
        return True
    
    return False


def determine_next_agent(state: ChatState) -> str:
    """
    Simplified agent routing based on transition markers
    
    Args:
        state: Current ChatState
        
    Returns:
        Next agent node name or routing decision
    """
    
    # Check if session is active
    if not state.active:
        logger.info("Session inactive, ending workflow")
        return "end"
    
    # If we have a new user message to process, continue with current agent
    if state.last_user_message and state.messages:
        # Check if the last message is from AI and we need to clear the user message
        if state.messages[-1].type == "ai":
            # Clear user message after AI response to prevent loops
            logger.info("Clearing user message after AI response", 
                       last_user_message=state.last_user_message[:50])
            state.last_user_message = None
    
    # Check for transitions based on AI responses
    if state.messages and state.messages[-1].type == "ai":
        last_message = state.messages[-1]
        last_agent = last_message.metadata.get("agent", "unknown")
        
        logger.info("Checking transitions", 
                   last_agent=last_agent,
                   content_preview=last_message.content[:100],
                   has_gamemaster_marker=GAMEMASTER_MARKER in last_message.content,
                   has_story_creator_marker=STORY_CREATOR_MARKER in last_message.content)

        # **NEW: If user responds to gamemaster options, stay with gamemaster**
        if last_agent == "gamemaster" and GAMEMASTER_MARKER in last_message.content:
            logger.info("User responding to gamemaster options - staying with gamemaster")
            return "gamemaster"        
        
        # Simple marker-based routing with agent verification
        if should_transition_to_gamemaster(state):
            logger.info("Transitioning to gamemaster")
            return "gamemaster"
        
        if should_transition_to_story_creator(state):
            logger.info("Transitioning to story_creator")
            return "story_creator"
    
    # If no user message and no transitions, wait for input
    if not state.last_user_message:
        logger.info("No user message, waiting for input")
        return "wait"
    
    # Continue with current agent or default to story creator
    current = state.current_agent or "story_creator"
    logger.info("Continuing with current agent", current_agent=current)
    return current          