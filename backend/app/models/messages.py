"""
TextRPG Message Models
Pydantic Models für Chat Messages und Communication
"""

from typing import Literal, Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class ChatMessage(BaseModel):
    """
    Basic Chat Message Model für Phase 1
    Kompatibel mit LangChain BaseMessage Structure
    """
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: Literal["human", "ai", "system"] = Field(
        description="Message Type - human (user), ai (assistant), system (internal)"
    )
    content: str = Field(
        description="Message Content/Text"
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Metadata für erweiterte Features
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata (agent info, tokens, etc.)"
    )

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class StreamingChunk(BaseModel):
    """
    Model für Streaming Response Chunks
    """
    
    content: str = Field(description="Chunk Content")
    chunk_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    is_final: bool = Field(default=False, description="Whether this is the final chunk")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ChatRequest(BaseModel):
    """
    Request Model für Chat Endpoints
    """
    
    session_id: Optional[str] = Field(
        default=None,
        description="Session ID - wird automatisch generiert wenn nicht angegeben"
    )
    message: str = Field(
        description="User Message Content",
        min_length=1,
        max_length=2000
    )
    
    # Optional für Phase 1, aber vorbereitet für Phase 2
    user_id: Optional[str] = Field(
        default=None,
        description="User ID für Multi-User Support (Phase 2)"
    )


class ChatResponse(BaseModel):
    """
    Response Model für Chat Endpoints
    """
    
    session_id: str = Field(description="Session ID")
    message: ChatMessage = Field(description="AI Response Message")
    status: Literal["success", "error", "processing"] = Field(default="success")
    
    # Metadata für debugging/monitoring
    processing_time_ms: Optional[int] = Field(
        default=None,
        description="Processing time in milliseconds"
    )
    
    # Error handling
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if status is 'error'"
    )


class StreamingResponse(BaseModel):
    """
    Response Model für Server-Sent Events
    """
    
    session_id: str = Field(description="Session ID")
    chunk: StreamingChunk = Field(description="Streaming Chunk")
    status: Literal["streaming", "completed", "error"] = Field(default="streaming")
    
    # Total progress info (optional)
    total_chunks: Optional[int] = Field(default=None)
    current_chunk: Optional[int] = Field(default=None) 