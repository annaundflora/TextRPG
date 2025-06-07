"""
TextRPG Agent Nodes - Phase 2
Agent-spezifische Node-Funktionen für LangGraph Workflow
"""

from typing import Dict, Any
import structlog
from datetime import datetime

from ..models import ChatState, ChatMessage, create_human_message, create_ai_message, AgentType
from ..agents import StoryCreatorAgent, GamemasterAgent
from ..config import settings
from langchain_openai import ChatOpenAI

logger = structlog.get_logger()


async def story_creator_node(state: ChatState) -> Dict[str, Any]:
    """
    Story Creator Node für Phase 2 - Kapitel-Generierung
    
    Args:
        state: Current ChatState mit Agent-Management
        
    Returns:
        Updated state dict mit Story Creator Response und Transition-Detection
    """
    
    try:
        logger.info("Processing Story Creator node", 
                   session_id=state.session_id,
                   current_agent=state.current_agent)
        
        # Set current agent
        if state.current_agent != "story_creator":
            state.switch_agent("story_creator", "node_entry")
        
        # Validate state
        if not state.last_user_message:
            logger.warning("No user message to process in Story Creator", 
                          session_id=state.session_id)
            return {"processing": False}
        
        # User message handling
        if not state.messages or state.messages[-1].type != "human":
            user_message = create_human_message(state.last_user_message)
            state.add_message(user_message)
        
        # Initialize LLM
        llm = ChatOpenAI(
            base_url=settings.openrouter_base_url,
            api_key=settings.openrouter_api_key,
            model=settings.llm_creator
        )
        
        # Create agent
        story_agent = StoryCreatorAgent(llm)
        
        # Get messages and context
        recent_messages = state.get_recent_messages(limit=10)
        agent_context = state.get_agent_context()
        
        # Generate response
        response_text, should_transition, transition_trigger = story_agent.process_message(
            recent_messages, agent_context
        )
        
        # Create AI response
        ai_response = create_ai_message(
            response_text,
            metadata={
                "agent": "story_creator",
                "model": settings.llm_creator,
                "should_transition": should_transition,
                "transition_trigger": transition_trigger
            }
        )
        
        # Add to conversation
        state.add_message(ai_response)
        
        # Update context
        story_context = response_text[:500] + "..." if len(response_text) > 500 else response_text
        state.update_story_context(story_context)
        
        logger.info("Story Creator response generated", 
                   session_id=state.session_id,
                   response_length=len(response_text),
                   should_transition=should_transition,
                   transition_trigger=transition_trigger)
        
        # Handle transition
        if should_transition and transition_trigger:
            state.switch_agent(
                "gamemaster", 
                transition_trigger,
                f"Story Creator → Gamemaster: {transition_trigger}"
            )
        else:
            # Clear transition trigger if no transition needed
            state.transition_trigger = None
            logger.info("Agent transition triggered", 
                       session_id=state.session_id,
                       from_agent="story_creator",
                       to_agent="gamemaster",
                       trigger=transition_trigger)
        
        # Clear user message after processing to prevent loops
        state.last_user_message = None
        
        # Return updated state
        return {
            "messages": state.messages,
            "processing": False,
            "last_user_message": None,  # Clear to prevent loops
            "last_updated": datetime.utcnow(),
            "total_messages": state.total_messages,
            "current_agent": state.current_agent,
            "transition_trigger": state.transition_trigger,
            "story_context": state.story_context,
            "agent_handoff_context": state.agent_handoff_context,
            "metadata": {
                **state.metadata,
                "last_agent": "story_creator",
                "phase": "2 - Agent Based"
            }
        }
        
    except Exception as e:
        logger.error("Error in Story Creator node", 
                    session_id=state.session_id,
                    error=str(e))
        
        # Create error response
        error_message = create_ai_message(
            f"Entschuldigung, es gab ein Problem beim Erstellen der Geschichte. "
            f"Bitte versuche es erneut.",
            metadata={"error": True, "agent": "story_creator", "error_type": "story_generation_error"}
        )
        
        state.add_message(error_message)
        
        return {
            "messages": state.messages,
            "processing": False,
            "last_updated": datetime.utcnow(),
            "total_messages": state.total_messages,
            "metadata": {
                **state.metadata,
                "last_error": {"agent": "story_creator", "message": str(e)},
                "last_error_time": datetime.utcnow().isoformat()
            }
        }


async def gamemaster_node(state: ChatState) -> Dict[str, Any]:
    """
    Gamemaster Node für Phase 2 - Spieleraktions-Verarbeitung
    
    Args:
        state: Current ChatState mit Agent-Management
        
    Returns:
        Updated state dict mit Gamemaster Response und Transition-Detection
    """
    
    try:
        logger.info("Processing Gamemaster node", 
                   session_id=state.session_id,
                   current_agent=state.current_agent)
        
        # Set current agent
        if state.current_agent != "gamemaster":
            state.switch_agent("gamemaster", "node_entry")
        
        # Validate state
        if not state.last_user_message:
            logger.warning("No user message to process in Gamemaster", 
                          session_id=state.session_id)
            return {"processing": False}
        
        # User message handling
        if not state.messages or state.messages[-1].type != "human":
            user_message = create_human_message(state.last_user_message)
            state.add_message(user_message)
        
        # Initialize LLM
        llm = ChatOpenAI(
            base_url=settings.openrouter_base_url,
            api_key=settings.openrouter_api_key,
            model=settings.llm_gamemaster
        )
        
        # Create agent
        gamemaster_agent = GamemasterAgent(llm)
        
        # Get messages and context
        recent_messages = state.get_recent_messages(limit=10)
        agent_context = state.get_agent_context()
        
        # Generate response
        response_text, should_transition, transition_trigger = gamemaster_agent.process_message(
            recent_messages, agent_context
        )
        
        # Create AI response
        ai_response = create_ai_message(
            response_text,
            metadata={
                "agent": "gamemaster",
                "model": settings.llm_gamemaster,
                "should_transition": should_transition,
                "transition_trigger": transition_trigger
            }
        )
        
        # Add to conversation
        state.add_message(ai_response)
        
        # Basic character tracking
        if "level" in response_text.lower() or "skill" in response_text.lower():
            char_updates = {"last_action": state.last_user_message}
            state.update_character_info(char_updates)
        
        logger.info("Gamemaster response generated", 
                   session_id=state.session_id,
                   response_length=len(response_text),
                   should_transition=should_transition,
                   transition_trigger=transition_trigger)
        
        # Handle transition
        if should_transition and transition_trigger:
            state.switch_agent(
                "story_creator", 
                transition_trigger,
                f"Gamemaster → Story Creator: {transition_trigger}"
            )
        else:
            # Clear transition trigger if no transition needed
            state.transition_trigger = None
            logger.info("Agent transition triggered", 
                       session_id=state.session_id,
                       from_agent="gamemaster",
                       to_agent="story_creator",
                       trigger=transition_trigger)
        
        # Clear user message after processing to prevent loops
        state.last_user_message = None
        
        # Return updated state
        return {
            "messages": state.messages,
            "processing": False,
            "last_user_message": None,  # Clear to prevent loops
            "last_updated": datetime.utcnow(),
            "total_messages": state.total_messages,
            "current_agent": state.current_agent,
            "transition_trigger": state.transition_trigger,
            "story_context": state.story_context,
            "character_info": state.character_info,
            "agent_handoff_context": state.agent_handoff_context,
            "metadata": {
                **state.metadata,
                "last_agent": "gamemaster",
                "phase": "2 - Agent Based"
            }
        }
        
    except Exception as e:
        logger.error("Error in Gamemaster node", 
                    session_id=state.session_id,
                    error=str(e))
        
        # Create error response
        error_message = create_ai_message(
            f"Entschuldigung, es gab ein Problem beim Verarbeiten deiner Aktion. "
            f"Bitte versuche es erneut.",
            metadata={"error": True, "agent": "gamemaster", "error_type": "action_processing_error"}
        )
        
        state.add_message(error_message)
        
        return {
            "messages": state.messages,
            "processing": False,
            "last_updated": datetime.utcnow(),
            "total_messages": state.total_messages,
            "metadata": {
                **state.metadata,
                "last_error": {"agent": "gamemaster", "message": str(e)},
                "last_error_time": datetime.utcnow().isoformat()
            }
        }


def determine_next_agent(state: ChatState) -> str:
    """
    Phase 2: Agent transition logic basierend auf State und Transition-Triggern
    
    Args:
        state: Current ChatState
        
    Returns:
        Next agent node name
    """
    
    # Check if session is active
    if not state.active:
        logger.info("Session inactive, ending workflow", session_id=state.session_id)
        return "end"
    
    # Check for processing state
    if not state.processing and not state.last_user_message:
        logger.info("No processing needed, waiting for user input", session_id=state.session_id)
        return "wait"
    
    # Determine based on current agent and transition trigger
    current_agent = state.current_agent
    transition_trigger = state.transition_trigger
    
    logger.info("Determining next agent", 
               session_id=state.session_id,
               current_agent=current_agent,
               transition_trigger=transition_trigger,
               has_user_message=bool(state.last_user_message))
    
    # If no agent set yet, start with Story Creator
    if not current_agent:
        logger.info("No current agent, starting with Story Creator", session_id=state.session_id)
        return "story_creator"
    
    # Check transition triggers for agent switching 
    # BUT only if we have user input to process AND a valid transition trigger
    if transition_trigger == "handlungsoptionen_präsentiert" and state.last_user_message:
        logger.info("Transition to Gamemaster (handlungsoptionen)", session_id=state.session_id)
        return "gamemaster"
    
    if transition_trigger == "neues_kapitel_benötigt" and state.last_user_message:
        logger.info("Transition to Story Creator (neues_kapitel)", session_id=state.session_id)
        return "story_creator"
    
    # Default: continue with current agent if there's user input to process
    if state.last_user_message and state.processing:
        next_agent = current_agent if current_agent else "story_creator"
        logger.info("Continuing with current agent", 
                   session_id=state.session_id,
                   next_agent=next_agent)
        return next_agent
    
    # Fallback
    logger.info("Fallback to wait state", session_id=state.session_id)
    return "wait" 