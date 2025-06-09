"""
TextRPG State Models - VEREINFACHTE VERSION
Minimales State Management - LLM verwaltet den narrativen Kontext
"""

from typing import List, Optional, Dict, Any, Literal, TypedDict
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

from .messages import ChatMessage


# Agent Types
AgentType = Literal["setup_agent", "gameplay_agent"]

# Story Phase für Flow Control  
StoryPhase = Literal["setup", "gameplay", "end"]

# End Trigger Types für Session Management
EndTrigger = Literal["quest_complete", "player_death", "explicit_end", "session_limit"]


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
    VEREINFACHTES State Model - Minimales Session-Tracking
    
    Der narrative Kontext wird vom LLM verwaltet, nicht im State!
    """
    
    # Core Session Data
    session_id: str = Field(description="Unique Session Identifier")
    messages: List[ChatMessage] = Field(
        default_factory=list,
        description="Conversation history"
    )
    
    # Flow Control
    story_phase: StoryPhase = Field(
        default="setup",
        description="Current story phase: setup|gameplay|end"
    )
    
    # Agent Management
    current_agent: Optional[AgentType] = Field(
        default="setup_agent",
        description="Currently active agent"
    )
    
    # Handoff für Agent-Transitions
    handoff_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Temporary data for agent transitions"
    )
    
    # Progress Tracking (nur Zahlen!)
    chapter_count: int = Field(
        default=0,
        description="Current chapter number"
    )
    
    interaction_count: int = Field(
        default=0,
        description="Total interactions in session"
    )
    
    # Session Management
    active: bool = Field(default=True, description="Whether session is active")
    processing: bool = Field(default=False, description="Processing state")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    # End Trigger
    end_trigger: Optional[EndTrigger] = Field(
        default=None,
        description="Reason for session end"
    )
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def add_message(self, message: ChatMessage) -> None:
        """Fügt Message hinzu und aktualisiert Timestamps"""
        self.messages.append(message)
        self.last_updated = datetime.utcnow()
        
        # Increment interaction count nur bei User-Messages
        if message.type == "human":
            self.interaction_count += 1
    
    def get_recent_messages(self, limit: int = 10) -> List[ChatMessage]:
        """Gibt die letzten N Messages zurück"""
        return self.messages[-limit:] if len(self.messages) > limit else self.messages


# TypedDict für LangGraph Compatibility
class ChatStateDict(TypedDict, total=False):
    """
    Vereinfachte TypedDict Version für LangGraph
    """
    session_id: str
    messages: List[ChatMessage]
    story_phase: StoryPhase
    current_agent: Optional[AgentType]
    handoff_data: Optional[Dict[str, Any]]
    chapter_count: int
    interaction_count: int
    active: bool
    processing: bool
    created_at: datetime
    last_updated: datetime
    end_trigger: Optional[EndTrigger]


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
    story_phase: StoryPhase = Field(default="setup")
    chapter_count: int = Field(default=0)
    interaction_count: int = Field(default=0)
    end_trigger: Optional[EndTrigger] = Field(default=None)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        } 