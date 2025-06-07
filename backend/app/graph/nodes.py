"""
TextRPG LangGraph Nodes
Node-Funktionen für LangGraph Workflow - Phase 1
"""

from typing import Dict, Any, List
import structlog
from datetime import datetime

from ..models import ChatState, ChatMessage, create_human_message, create_ai_message, AgentType
from ..services import get_langchain_llm_service, LLMServiceException
from ..agents import StoryCreatorAgent, GamemasterAgent
from ..config import settings
from langchain_openai import ChatOpenAI

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


# ===================================
# Phase 2: Agent-Specific Nodes
# ===================================

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
                   message_count=len(state.messages),
                   current_agent=state.current_agent)
        
        # Set current agent
        if state.current_agent != "story_creator":
            state.switch_agent("story_creator", "node_entry")
        
        # Validate state
        if not state.last_user_message:
            logger.warning("No user message to process in Story Creator", 
                          session_id=state.session_id)
            return {"processing": False}
        
        # User message sollte bereits im State sein
        if not state.messages or state.messages[-1].type != "human":
            user_message = create_human_message(state.last_user_message)
            state.add_message(user_message)
        
        # Initialize LLM für Story Creator
        llm = ChatOpenAI(
            base_url=settings.openrouter_base_url,
            api_key=settings.openrouter_api_key,
            model=settings.llm_creator
        )
        
        # Create Story Creator Agent
        story_agent = StoryCreatorAgent(llm)
        
        # Prepare messages (convert to LangChain format)
        recent_messages = state.get_recent_messages(limit=10)
        langchain_messages = []
        for msg in recent_messages:
            if msg.type == "human":
                langchain_messages.append({"role": "user", "content": msg.content})
            elif msg.type == "ai":
                langchain_messages.append({"role": "assistant", "content": msg.content})
        
        # Add agent context if available
        agent_context = state.get_agent_context()
        context_info = []
        if agent_context.get("story_context"):
            context_info.append(f"Story-Kontext: {agent_context['story_context']}")
        if agent_context.get("character_info"):
            char_info = agent_context['character_info']
            if char_info:
                context_info.append(f"Charakter: {char_info}")
        if agent_context.get("agent_handoff_context"):
            context_info.append(f"Kontext: {agent_context['agent_handoff_context']}")
        
        # Add context as system-level info if available
        if context_info:
            context_message = "KONTEXT: " + " | ".join(context_info)
            if langchain_messages:
                langchain_messages[0]["content"] = context_message + "\n\n" + langchain_messages[0]["content"]
        
        logger.info("Calling Story Creator Agent", 
                   session_id=state.session_id,
                   context_messages=len(langchain_messages),
                   agent_context=bool(context_info))
        
        # Generate Story Creator response
        response_text, should_transition, transition_trigger = story_agent.process_message(
            [msg for msg in recent_messages], agent_context
        )
        
        # Create AI response message
        ai_response = create_ai_message(
            response_text,
            metadata={
                "agent": "story_creator",
                "model": settings.llm_creator,
                "should_transition": should_transition,
                "transition_trigger": transition_trigger,
                "context_provided": bool(context_info)
            }
        )
        
        # Add AI response to conversation
        state.add_message(ai_response)
        
        # Update story context (first 500 chars of response)
        story_context = response_text[:500] + "..." if len(response_text) > 500 else response_text
        state.update_story_context(story_context)
        
        logger.info("Story Creator response generated", 
                   session_id=state.session_id,
                   response_length=len(response_text),
                   should_transition=should_transition,
                   transition_trigger=transition_trigger)
        
        # Handle agent transition
        if should_transition and transition_trigger:
            state.switch_agent(
                "gamemaster", 
                transition_trigger,
                f"Story Creator → Gamemaster: {transition_trigger}"
            )
            logger.info("Agent transition triggered", 
                       session_id=state.session_id,
                       from_agent="story_creator",
                       to_agent="gamemaster",
                       trigger=transition_trigger)
        
        # Update state
        return {
            "messages": state.messages,
            "processing": False,
            "last_updated": datetime.utcnow(),
            "total_messages": state.total_messages,
            "current_agent": state.current_agent,
            "transition_trigger": state.transition_trigger,
            "story_context": state.story_context,
            "agent_handoff_context": state.agent_handoff_context,
            "metadata": {
                **state.metadata,
                "last_agent": "story_creator",
                "last_model_used": settings.llm_creator,
                "last_completion_time": datetime.utcnow().isoformat(),
                "agent_transition": should_transition,
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
                   message_count=len(state.messages),
                   current_agent=state.current_agent)
        
        # Set current agent
        if state.current_agent != "gamemaster":
            state.switch_agent("gamemaster", "node_entry")
        
        # Validate state
        if not state.last_user_message:
            logger.warning("No user message to process in Gamemaster", 
                          session_id=state.session_id)
            return {"processing": False}
        
        # User message sollte bereits im State sein
        if not state.messages or state.messages[-1].type != "human":
            user_message = create_human_message(state.last_user_message)
            state.add_message(user_message)
        
        # Initialize LLM für Gamemaster
        llm = ChatOpenAI(
            base_url=settings.openrouter_base_url,
            api_key=settings.openrouter_api_key,
            model=settings.llm_gamemaster
        )
        
        # Create Gamemaster Agent
        gamemaster_agent = GamemasterAgent(llm)
        
        # Prepare messages
        recent_messages = state.get_recent_messages(limit=10)
        
        # Add agent context for Gamemaster
        agent_context = state.get_agent_context()
        context_info = []
        if agent_context.get("story_context"):
            context_info.append(f"Story-Kontext: {agent_context['story_context']}")
        if agent_context.get("character_info"):
            char_info = agent_context['character_info']
            if char_info:
                context_info.append(f"Charakter: {char_info}")
        if agent_context.get("agent_handoff_context"):
            context_info.append(f"Kontext: {agent_context['agent_handoff_context']}")
        
        logger.info("Calling Gamemaster Agent", 
                   session_id=state.session_id,
                   context_messages=len(recent_messages),
                   agent_context=bool(context_info))
        
        # Generate Gamemaster response
        response_text, should_transition, transition_trigger = gamemaster_agent.process_message(
            recent_messages, agent_context
        )
        
        # Create AI response message
        ai_response = create_ai_message(
            response_text,
            metadata={
                "agent": "gamemaster",
                "model": settings.llm_gamemaster,
                "should_transition": should_transition,
                "transition_trigger": transition_trigger,
                "context_provided": bool(context_info)
            }
        )
        
        # Add AI response to conversation
        state.add_message(ai_response)
        
        # Extract character info from response if possible
        # (Simplified - könnte in Zukunft intelligenter gemacht werden)
        if "level" in response_text.lower() or "skill" in response_text.lower():
            # Basic character info extraction
            char_updates = {"last_action": state.last_user_message}
            state.update_character_info(char_updates)
        
        logger.info("Gamemaster response generated", 
                   session_id=state.session_id,
                   response_length=len(response_text),
                   should_transition=should_transition,
                   transition_trigger=transition_trigger)
        
        # Handle agent transition
        if should_transition and transition_trigger:
            state.switch_agent(
                "story_creator", 
                transition_trigger,
                f"Gamemaster → Story Creator: {transition_trigger}"
            )
            logger.info("Agent transition triggered", 
                       session_id=state.session_id,
                       from_agent="gamemaster",
                       to_agent="story_creator",
                       trigger=transition_trigger)
        
        # Update state
        return {
            "messages": state.messages,
            "processing": False,
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
                "last_model_used": settings.llm_gamemaster,
                "last_completion_time": datetime.utcnow().isoformat(),
                "agent_transition": should_transition,
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
    if transition_trigger == "handlungsoptionen_präsentiert":
        logger.info("Transition to Gamemaster (handlungsoptionen)", session_id=state.session_id)
        return "gamemaster"
    
    if transition_trigger == "neues_kapitel_benötigt":
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