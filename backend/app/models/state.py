"""
TextRPG State Models
Pydantic Models für LangGraph State Management
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

from .messages import ChatMessage


class ChatSession(BaseModel):
    """
    Chat Session Model für Session Management
    """
    
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    
    # User Info (optional für Phase 1)
    user_id: Optional[str] = Field(default=None)
    
    # Session Configuration
    active: bool = Field(default=True)
    
    # Metadata
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Session-specific metadata"
    )
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ChatState(BaseModel):
    """
    LangGraph State Model für Phase 1 - Foundation Chatbot
    
    Dieses Model wird in Phase 2 um Agent-spezifische Felder erweitert:
    - current_agent: Optional[Literal["story_creator", "gamemaster"]]
    - transition_trigger: Optional[str]
    - story_context: Optional[str]
    - character_info: Optional[Dict[str, Any]]
    - agent_handoff_context: Optional[str]
    """
    
    # Core Session Data
    session_id: str = Field(description="Unique Session Identifier")
    messages: List[ChatMessage] = Field(
        default_factory=list,
        description="Conversation History"
    )
    
    # Basic State Management
    active: bool = Field(default=True, description="Whether session is active")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    # Current Processing Info
    processing: bool = Field(
        default=False, 
        description="Whether a request is currently being processed"
    )
    
    last_user_message: Optional[str] = Field(
        default=None,
        description="Last user input for processing"
    )
    
    # Basic Metadata für Phase 1
    total_messages: int = Field(
        default=0,
        description="Total number of messages in conversation"
    )
    
    # Extendable Metadata für Phase 2
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional state data"
    )
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def add_message(self, message: ChatMessage) -> None:
        """
        Fügt eine Message zum State hinzu und updated Metadata
        """
        self.messages.append(message)
        self.total_messages = len(self.messages)
        self.last_updated = datetime.utcnow()
        
        if message.type == "human":
            self.last_user_message = message.content
    
    def get_recent_messages(self, limit: int = 10) -> List[ChatMessage]:
        """
        Gibt die letzten N Messages zurück
        """
        return self.messages[-limit:] if len(self.messages) > limit else self.messages
    
    def clear_messages(self) -> None:
        """
        Löscht alle Messages (Session Reset)
        """
        self.messages = []
        self.total_messages = 0
        self.last_user_message = None
        self.last_updated = datetime.utcnow()


class StateUpdate(BaseModel):
    """
    Model für State Updates von LangGraph Nodes
    """
    
    session_id: str = Field(description="Session ID")
    
    # Optional Updates
    new_message: Optional[ChatMessage] = Field(default=None)
    processing: Optional[bool] = Field(default=None)
    metadata_update: Optional[Dict[str, Any]] = Field(default=None)
    
    # für Phase 2 vorbereitet
    agent_transition: Optional[str] = Field(default=None)


class SessionInfo(BaseModel):
    """
    Öffentliche Session Information (ohne sensitive Daten)
    """
    
    session_id: str
    active: bool
    message_count: int
    created_at: datetime
    last_activity: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        } 