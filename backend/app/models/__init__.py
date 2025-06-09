"""
TextRPG Models Package
Pydantic Models für State Management und API Communication
"""

from .messages import (
    ChatMessage,
    StreamingChunk,
    ChatRequest,
    ChatResponse,
    StreamingResponse
)

from .state import (
    ChatSession,
    ChatState,
    SessionInfo,
    AgentType
)

from .converters import (
    pydantic_to_langchain,
    langchain_to_pydantic,
    messages_to_langchain,
    messages_from_langchain,
    create_system_message,
    create_ai_message,
    create_human_message
)

__all__ = [
    # Message Models
    "ChatMessage",
    "StreamingChunk", 
    "ChatRequest",
    "ChatResponse",
    "StreamingResponse",
    
    # State Models
    "ChatSession",
    "ChatState", 
    "SessionInfo",
    "AgentType",
    
    # Converters
    "pydantic_to_langchain",
    "langchain_to_pydantic",
    "messages_to_langchain",
    "messages_from_langchain",
    "create_system_message",
    "create_ai_message",
    "create_human_message"
] 