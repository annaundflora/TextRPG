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
    ChatStateDict,
    SessionInfo,
    AgentType,
    StoryPhase,
    EndTrigger
)

from .commands import (
    CommandType,
    AgentCommand,
    create_goto_command,
    create_update_command
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
    
    # State Models - PRD Extended
    "ChatSession",
    "ChatState", 
    "ChatStateDict",
    "SessionInfo",
    "AgentType",
    "StoryPhase",
    "EndTrigger",
    
    # Command Pattern Models
    "CommandType",
    "AgentCommand", 
    "create_goto_command",
    "create_update_command",
    
    # Converters
    "pydantic_to_langchain",
    "langchain_to_pydantic",
    "messages_to_langchain",
    "messages_from_langchain",
    "create_system_message",
    "create_ai_message",
    "create_human_message"
] 