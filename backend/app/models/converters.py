"""
TextRPG Model Converters
Utility-Funktionen für Konvertierung zwischen Pydantic und LangChain Models
"""

from typing import List, Union
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.messages.base import BaseMessage as LangChainBaseMessage

from .messages import ChatMessage


def pydantic_to_langchain(message: ChatMessage) -> BaseMessage:
    """
    Konvertiert ChatMessage (Pydantic) zu LangChain BaseMessage
    
    Args:
        message: ChatMessage instance
        
    Returns:
        Entsprechende LangChain Message
    """
    
    if message.type == "human":
        return HumanMessage(
            content=message.content,
            additional_kwargs=message.metadata
        )
    elif message.type == "ai":
        return AIMessage(
            content=message.content,
            additional_kwargs=message.metadata
        )
    elif message.type == "system":
        return SystemMessage(
            content=message.content,
            additional_kwargs=message.metadata
        )
    else:
        raise ValueError(f"Unknown message type: {message.type}")


def langchain_to_pydantic(message: BaseMessage) -> ChatMessage:
    """
    Konvertiert LangChain BaseMessage zu ChatMessage (Pydantic)
    
    Args:
        message: LangChain BaseMessage instance
        
    Returns:
        ChatMessage instance
    """
    
    # Bestimme Message Type basierend auf LangChain Type
    if isinstance(message, HumanMessage):
        msg_type = "human"
    elif isinstance(message, AIMessage):
        msg_type = "ai"
    elif isinstance(message, SystemMessage):
        msg_type = "system"
    else:
        # Fallback für andere Message Types
        msg_type = "system"
    
    return ChatMessage(
        type=msg_type,
        content=message.content,
        metadata=getattr(message, 'additional_kwargs', {})
    )


def messages_to_langchain(messages: List[ChatMessage]) -> List[BaseMessage]:
    """
    Konvertiert Liste von ChatMessages zu LangChain Messages
    
    Args:
        messages: Liste von ChatMessage instances
        
    Returns:
        Liste von LangChain BaseMessage instances
    """
    return [pydantic_to_langchain(msg) for msg in messages]


def messages_from_langchain(messages: List[BaseMessage]) -> List[ChatMessage]:
    """
    Konvertiert Liste von LangChain Messages zu ChatMessages
    
    Args:
        messages: Liste von LangChain BaseMessage instances
        
    Returns:
        Liste von ChatMessage instances
    """
    return [langchain_to_pydantic(msg) for msg in messages]


def create_system_message(content: str, metadata: dict = None) -> ChatMessage:
    """
    Helper-Funktion für System Messages
    
    Args:
        content: System message content
        metadata: Optional metadata
        
    Returns:
        ChatMessage mit type="system"
    """
    return ChatMessage(
        type="system",
        content=content,
        metadata=metadata or {}
    )


def create_ai_message(content: str, metadata: dict = None) -> ChatMessage:
    """
    Helper-Funktion für AI Messages
    
    Args:
        content: AI message content
        metadata: Optional metadata (z.B. agent info, tokens, etc.)
        
    Returns:
        ChatMessage mit type="ai"
    """
    return ChatMessage(
        type="ai", 
        content=content,
        metadata=metadata or {}
    )


def create_human_message(content: str, metadata: dict = None) -> ChatMessage:
    """
    Helper-Funktion für Human Messages
    
    Args:
        content: Human message content
        metadata: Optional metadata
        
    Returns:
        ChatMessage mit type="human"
    """
    return ChatMessage(
        type="human",
        content=content, 
        metadata=metadata or {}
    ) 