"""
TextRPG State Models
Pydantic Models für LangGraph State Management
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

from .messages import ChatMessage


# Agent Types für Phase 2
AgentType = Literal["story_creator", "gamemaster"]


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
    LangGraph State Model für Phase 2 - Agent-Based TextRPG
    
    Erweitert um Agent-Management für Story Creator und Gamemaster Agents.
    """
    
    # Core Session Data
    session_id: str = Field(description="Unique Session Identifier")
    messages: List[ChatMessage] = Field(
        default_factory=list,
        description="Conversation History"
    )
    
    # Phase 2: Agent Management
    current_agent: Optional[AgentType] = Field(
        default=None,
        description="Aktuell aktiver Agent (story_creator/gamemaster)"
    )
    
    transition_trigger: Optional[str] = Field(
        default=None,
        description="Grund für den letzten Agent-Switch"
    )
    
    # Phase 2: Context Preservation für Agent-Handoff
    story_context: Optional[str] = Field(
        default=None,
        description="Aktueller Story-Kontext für Kontinuität zwischen Agents"
    )
    
    character_info: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Spieler-Charakterdaten vom Gamemaster"
    )
    
    agent_handoff_context: Optional[str] = Field(
        default=None,
        description="Explizite Übergabe-Informationen zwischen Agents"
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
    
    # Phase 2: Agent Management Methods
    def switch_agent(self, new_agent: AgentType, trigger: str, handoff_context: Optional[str] = None) -> None:
        """
        Wechselt den aktiven Agent und updated Transition-Info.
        
        Args:
            new_agent: Der neue Agent (story_creator/gamemaster)
            trigger: Grund für den Agent-Switch
            handoff_context: Optional Kontext-Info für den neuen Agent
        """
        self.current_agent = new_agent
        self.transition_trigger = trigger
        self.agent_handoff_context = handoff_context
        self.last_updated = datetime.utcnow()
    
    def update_story_context(self, context: str) -> None:
        """
        Updated den Story-Kontext für Agent-Kontinuität.
        """
        self.story_context = context
        self.last_updated = datetime.utcnow()
    
    def update_character_info(self, character_updates: Dict[str, Any]) -> None:
        """
        Updated Spieler-Charakterdaten.
        """
        if self.character_info is None:
            self.character_info = {}
        self.character_info.update(character_updates)
        self.last_updated = datetime.utcnow()
    
    def get_agent_context(self) -> Dict[str, Any]:
        """
        Gibt den vollständigen Agent-Kontext zurück.
        """
        return {
            "current_agent": self.current_agent,
            "transition_trigger": self.transition_trigger,
            "story_context": self.story_context,
            "character_info": self.character_info,
            "agent_handoff_context": self.agent_handoff_context
        }
    
    def reset_agent_state(self) -> None:
        """
        Resettet alle Agent-spezifischen Felder (bei Session-Reset).
        """
        self.current_agent = None
        self.transition_trigger = None
        self.story_context = None
        self.character_info = {}
        self.agent_handoff_context = None
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
    
    # Phase 2: Agent Management Updates
    new_agent: Optional[AgentType] = Field(default=None)
    transition_trigger: Optional[str] = Field(default=None)
    story_context: Optional[str] = Field(default=None)
    character_info_update: Optional[Dict[str, Any]] = Field(default=None)
    agent_handoff_context: Optional[str] = Field(default=None)


class SessionInfo(BaseModel):
    """
    Öffentliche Session Information (ohne sensitive Daten)
    """
    
    session_id: str
    active: bool
    message_count: int
    created_at: datetime
    last_activity: datetime
    
    # Phase 2: Agent Information
    current_agent: Optional[AgentType] = Field(default=None)
    has_story_context: bool = Field(default=False)
    has_character_info: bool = Field(default=False)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        } 