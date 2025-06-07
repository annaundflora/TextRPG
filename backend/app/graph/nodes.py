"""
TextRPG LangGraph Nodes
Node-Funktionen für LangGraph Workflow - Phase 1
"""

from typing import Dict, Any, List
import structlog
from datetime import datetime

from ..models import ChatState, ChatMessage, create_human_message, create_ai_message
from ..services import get_langchain_llm_service, LLMServiceException

logger = structlog.get_logger()


async def generic_chat_node(state: ChatState) -> Dict[str, Any]:
    """
    Generic Chat Node für Phase 1 mit LangChain LLM Service
    Verarbeitet User-Input und generiert AI-Response ohne Agent-Switching
    Vollständiges LangSmith Tracing durch LangChain Integration
    
    Args:
        state: Current ChatState
        
    Returns:
        Updated state dict
    """
    
    try:
        logger.info("Processing generic chat node with LangChain LLM", 
                   session_id=state.session_id,
                   message_count=len(state.messages),
                   last_user_message=state.last_user_message)
        
        # Validate state
        if not state.last_user_message:
            logger.warning("No user message to process", session_id=state.session_id)
            return {"processing": False}
        
        # User message sollte bereits vom caller (chat.py/session_manager) hinzugefügt worden sein
        # Zusätzliche Validierung, aber keine doppelte Hinzufügung
        if not state.messages or state.messages[-1].type != "human":
            logger.warning("Expected user message in conversation history", 
                          session_id=state.session_id,
                          last_message_type=state.messages[-1].type if state.messages else "none")
            # Fallback: Add user message if somehow missing
            user_message = create_human_message(state.last_user_message)
            state.add_message(user_message)
        
        # Get LangChain LLM Service (for LangSmith tracing)
        llm_service = get_langchain_llm_service()
        
        # Prepare messages for LLM (get recent context)
        recent_messages = state.get_recent_messages(limit=10)
        
        logger.info("Calling LangChain LLM for chat completion", 
                   session_id=state.session_id,
                   context_messages=len(recent_messages),
                   langsmith_tracing=True)
        
        # Generate AI response mit LangChain (wird von LangSmith getrackt)
        ai_response = await llm_service.chat_completion(
            messages=recent_messages,
            session_id=state.session_id,  # Session-Tracing für LangSmith
            temperature=0.7,
            max_tokens=1500
        )
        
        # Add AI response to conversation
        state.add_message(ai_response)
        
        logger.info("LangChain chat completion successful", 
                   session_id=state.session_id,
                   response_length=len(ai_response.content),
                   model_used=ai_response.metadata.get("model", "unknown"),
                   langchain_traced=True)
        
        # Update state
        return {
            "messages": state.messages,
            "processing": False,
            "last_updated": datetime.utcnow(),
            "total_messages": state.total_messages,
            "metadata": {
                **state.metadata,
                "last_model_used": ai_response.metadata.get("model"),
                "last_response_tokens": ai_response.metadata.get("usage", {}).get("completion_tokens"),
                "last_completion_time": datetime.utcnow().isoformat(),
                "langchain_service": True,
                "langsmith_traced": True
            }
        }
        
    except LLMServiceException as e:
        logger.error("LangChain LLM service error in chat node", 
                    session_id=state.session_id,
                    error_type=e.error_type.value,
                    error_message=e.message)
        
        # Create error response message
        error_message = create_ai_message(
            f"Entschuldigung, es gab ein Problem bei der Verarbeitung deiner Nachricht. "
            f"Fehler: {e.message}",
            metadata={"error": True, "error_type": e.error_type.value, "langchain_service": True}
        )
        
        state.add_message(error_message)
        
        return {
            "messages": state.messages,
            "processing": False,
            "last_updated": datetime.utcnow(),
            "total_messages": state.total_messages,
            "metadata": {
                **state.metadata,
                "last_error": e.to_dict(),
                "last_error_time": datetime.utcnow().isoformat(),
                "langchain_service": True
            }
        }
        
    except Exception as e:
        logger.error("Unexpected error in LangChain chat node", 
                    session_id=state.session_id,
                    error=str(e))
        
        # Create generic error response
        error_message = create_ai_message(
            "Entschuldigung, es gab einen unerwarteten Fehler. Bitte versuche es erneut.",
            metadata={"error": True, "error_type": "unexpected_error", "langchain_service": True}
        )
        
        state.add_message(error_message)
        
        return {
            "messages": state.messages,
            "processing": False,
            "last_updated": datetime.utcnow(),
            "total_messages": state.total_messages,
            "metadata": {
                **state.metadata,
                "last_error": {"type": "unexpected_error", "message": str(e)},
                "last_error_time": datetime.utcnow().isoformat(),
                "langchain_service": True
            }
        }


async def start_node(state: ChatState) -> Dict[str, Any]:
    """
    Start Node für neue Sessions
    Initialisiert Session und gibt Willkommens-Nachricht
    
    Args:
        state: Initial ChatState
        
    Returns:
        Updated state dict mit Willkommens-Message
    """
    
    try:
        logger.info("Initializing new chat session", session_id=state.session_id)
        
        # Check if this is truly a new session (no messages)
        if not state.messages:
            welcome_message = create_ai_message(
                "Hallo! Willkommen beim TextRPG-Chat. Ich bin dein virtueller Gesprächspartner. "
                "Wie kann ich dir heute helfen?",
                metadata={
                    "node": "start_node",
                    "session_initialized": True,
                    "phase": "1 - Foundation Chatbot"
                }
            )
            
            state.add_message(welcome_message)
            
            logger.info("Session initialized with welcome message", 
                       session_id=state.session_id)
        
        return {
            "messages": state.messages,
            "processing": False,
            "active": True,
            "last_updated": datetime.utcnow(),
            "total_messages": state.total_messages,
            "metadata": {
                **state.metadata,
                "session_initialized": True,
                "initialization_time": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error("Error in start node", 
                    session_id=state.session_id,
                    error=str(e))
        
        # Fallback welcome message
        fallback_message = create_ai_message(
            "Hallo! Willkommen beim TextRPG-Chat.",
            metadata={"error": True, "fallback": True}
        )
        
        state.add_message(fallback_message)
        
        return {
            "messages": state.messages,
            "processing": False,
            "active": True,
            "last_updated": datetime.utcnow(),
            "total_messages": state.total_messages,
            "metadata": {
                **state.metadata,
                "initialization_error": str(e),
                "initialization_time": datetime.utcnow().isoformat()
            }
        }


def should_continue(state: ChatState) -> str:
    """
    Conditional Edge Funktion - bestimmt den nächsten Node
    Für Phase 1: Immer weiter zum Chat Node (kein Agent-Switching)
    
    Args:
        state: Current ChatState
        
    Returns:
        Next node name
    """
    
    # Check if session is active
    if not state.active:
        logger.info("Session inactive, ending workflow", session_id=state.session_id)
        return "end"
    
    # Check if there's a user message to process
    if state.last_user_message and state.processing:
        logger.info("User message detected, continuing to chat", 
                   session_id=state.session_id)
        return "chat"
    
    # Default: wait for user input
    logger.info("Waiting for user input", session_id=state.session_id)
    return "wait"


# Phase 2 Vorbereitung - Agent-Switching Logic (auskommentiert)
"""
def determine_next_agent(state: ChatState) -> str:
    # Phase 2: Agent transition logic
    # Analyze last AI response for transition triggers
    
    if not state.messages:
        return "story_creator"
    
    last_message = state.messages[-1]
    
    # Story Creator → Gamemaster trigger
    if "--- HANDLUNGSOPTIONEN ---" in last_message.content:
        return "gamemaster"
    
    # Gamemaster → Story Creator trigger  
    if "--- STORY CREATOR ÜBERGANG ---" in last_message.content:
        return "story_creator"
    
    # Default: continue with current agent
    return state.metadata.get("current_agent", "story_creator")
""" 