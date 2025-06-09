"""
Agent Node Functions für LangGraph Integration
Vereinfachte Wrapper für Setup- und Gameplay-Agents
"""

from typing import Dict, Any, Union, Literal
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.types import Command
from langchain_openai import ChatOpenAI
import logging

from ..agents.setup_agent import SetupAgent
from ..agents.gameplay_agent import GameplayAgent
from ..config import settings

logger = logging.getLogger(__name__)


# Globale Agent-Instanzen
_setup_agent = None
_gameplay_agent = None


async def get_setup_agent() -> SetupAgent:
    """Singleton Setup Agent mit LLM"""
    global _setup_agent
    if _setup_agent is None:
        llm = ChatOpenAI(
            base_url=settings.openrouter_base_url,
            api_key=settings.openrouter_api_key,
            model=settings.llm_creator  # Setup nutzt Creator Model
        )
        _setup_agent = SetupAgent(llm)
    return _setup_agent


async def get_gameplay_agent() -> GameplayAgent:
    """Singleton Gameplay Agent mit LLM"""
    global _gameplay_agent
    if _gameplay_agent is None:
        llm = ChatOpenAI(
            base_url=settings.openrouter_base_url,
            api_key=settings.openrouter_api_key,
            model=settings.llm_gamemaster  # Gameplay nutzt Gamemaster Model
        )
        _gameplay_agent = GameplayAgent(llm)
    return _gameplay_agent


async def setup_agent_node(state: Dict[str, Any]) -> Union[Command[Literal["gameplay_agent"]], Dict[str, Any]]:
    """
    Setup Agent Node für LangGraph
    Returns: Command object für Transition oder updated state dict
    """
    try:
        logger.info("Setup Agent Node started", extra={"session_id": state.get("session_id")})
        
        agent = await get_setup_agent()
        messages = state.get("messages", [])
        
        # Agent process_message ruft auf - kann Command oder string zurückgeben
        result = agent.process_message(messages, state)
        
        if isinstance(result, Command):
            # LangGraph Command - return direkt für automatische Transition
            logger.info("Setup Agent returning Command for transition", 
                       extra={"session_id": state.get("session_id")})
            return result
        else:
            # String response - erstelle AIMessage und update state
            ai_message = AIMessage(content=result)
            updated_messages = messages + [ai_message]
            
            logger.info("Setup Agent returning updated state", 
                       extra={"session_id": state.get("session_id")})
            
            return {
                **state,
                "messages": updated_messages,
                "current_agent": "setup_agent"
            }
            
    except Exception as e:
        logger.error("Error in setup_agent_node", 
                    extra={"session_id": state.get("session_id"), "error": str(e)},
                    exc_info=True)
        
        error_message = AIMessage(content=f"Ein Fehler ist aufgetreten: {str(e)}")
        return {
            **state,
            "messages": state.get("messages", []) + [error_message]
        }


async def gameplay_agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Gameplay Agent Node für LangGraph
    Returns: Updated state dict
    """
    try:
        logger.info("Gameplay Agent Node started", extra={"session_id": state.get("session_id")})
        
        agent = await get_gameplay_agent()
        messages = state.get("messages", [])
        
        # Agent process_message ruft auf - returned string
        result = agent.process_message(messages, state)
        
        # String response - erstelle AIMessage und update state
        ai_message = AIMessage(content=result)
        updated_messages = messages + [ai_message]
        
        logger.info("Gameplay Agent returning updated state", 
                   extra={"session_id": state.get("session_id")})
        
        return {
            **state,
            "messages": updated_messages,
            "current_agent": "gameplay_agent",
            "interaction_count": state.get("interaction_count", 0) + 1
        }
        
    except Exception as e:
        logger.error("Error in gameplay_agent_node", 
                    extra={"session_id": state.get("session_id"), "error": str(e)},
                    exc_info=True)
        
        error_message = AIMessage(content=f"Ein Fehler ist aufgetreten: {str(e)}")
        return {
            **state,
            "messages": state.get("messages", []) + [error_message]
        } 