"""
TextRPG State Models - Simplified for MVP
Pydantic Models für LangGraph State Management
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

from .messages import ChatMessage


# Agent Types
AgentType = Literal["story_creator", "gamemaster"]


class ChatSession(BaseModel):
    """
    Chat Session Model für Session Management
    """
    
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    active: bool = Field(default=True)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ChatState(BaseModel):
    """
    Simplified LangGraph State Model for MVP
    
    Nur die essentiellen Felder für Agent-basiertes TextRPG.
    """
    
    # Core Session Data
    session_id: str = Field(description="Unique Session Identifier")
    messages: List[ChatMessage] = Field(
        default_factory=list,
        description="Conversation History"
    )
    
    # Agent Management
    current_agent: Optional[AgentType] = Field(
        default="story_creator",
        description="Currently active agent"
    )
    
    # Processing State
    processing: bool = Field(
        default=False, 
        description="Whether a request is currently being processed"
    )
    
    last_user_message: Optional[str] = Field(
        default=None,
        description="Last user input for processing"
    )
    
    # Basic metadata
    active: bool = Field(default=True, description="Whether session is active")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def add_message(self, message: ChatMessage) -> None:
        """
        Fügt eine Message zum State hinzu
        """
        self.messages.append(message)
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
        self.last_user_message = None
        self.last_updated = datetime.utcnow()
    
    def switch_agent(self, new_agent: AgentType) -> None:
        """
        Wechselt den aktiven Agent
        """
        self.current_agent = new_agent
        self.last_updated = datetime.utcnow()


class SessionInfo(BaseModel):
    """
    Öffentliche Session Information
    """
    
    session_id: str
    active: bool
    message_count: int
    created_at: datetime
    last_activity: datetime
    current_agent: Optional[AgentType] = Field(default=None)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        } 