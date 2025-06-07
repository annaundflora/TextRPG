"""
TextRPG Session Manager
Verwaltet Chat Sessions und LangGraph State
"""

from typing import Dict, Optional, Any
import structlog
from datetime import datetime
import uuid

from ..models import ChatState, ChatMessage, create_human_message
from .workflow import get_workflow

logger = structlog.get_logger()


class SessionManager:
    """
    Verwaltet aktive Chat Sessions und deren State
    In-Memory Storage für Phase 1 (Phase 2: persistent storage)
    """
    
    def __init__(self):
        """Initialisiert Session Manager"""
        self.active_sessions: Dict[str, ChatState] = {}
        self.workflow = None
    
    async def initialize(self) -> None:
        """Initialisiert Workflow"""
        if self.workflow is None:
            self.workflow = get_workflow()
            logger.info("Session Manager initialized with workflow")
    
    def create_session(self, session_id: Optional[str] = None) -> str:
        """
        Erstellt neue Chat Session
        
        Args:
            session_id: Optional session ID (auto-generated if None)
            
        Returns:
            Session ID
        """
        
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        # Create initial state
        state = ChatState(
            session_id=session_id,
            messages=[],
            active=True,
            created_at=datetime.utcnow(),
            last_updated=datetime.utcnow(),
            processing=False,
            total_messages=0,
            metadata={}
        )
        
        self.active_sessions[session_id] = state
        
        logger.info("New session created", session_id=session_id)
        return session_id
    
    def get_session(self, session_id: str) -> Optional[ChatState]:
        """
        Holt bestehende Session
        
        Args:
            session_id: Session ID
            
        Returns:
            ChatState oder None wenn nicht gefunden
        """
        
        session = self.active_sessions.get(session_id)
        if session:
            logger.debug("Session retrieved", session_id=session_id)
        else:
            logger.warning("Session not found", session_id=session_id)
        
        return session
    
    def update_session(self, session_id: str, state: ChatState) -> bool:
        """
        Updated bestehende Session
        
        Args:
            session_id: Session ID
            state: Updated ChatState
            
        Returns:
            True wenn erfolgreich updated
        """
        
        if session_id in self.active_sessions:
            state.last_updated = datetime.utcnow()
            self.active_sessions[session_id] = state
            logger.debug("Session updated", session_id=session_id)
            return True
        else:
            logger.warning("Cannot update non-existent session", session_id=session_id)
            return False
    
    def delete_session(self, session_id: str) -> bool:
        """
        Löscht Session
        
        Args:
            session_id: Session ID
            
        Returns:
            True wenn erfolgreich gelöscht
        """
        
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            logger.info("Session deleted", session_id=session_id)
            return True
        else:
            logger.warning("Cannot delete non-existent session", session_id=session_id)
            return False
    
    async def process_message(
        self,
        session_id: str,
        user_message: str
    ) -> ChatState:
        """
        Verarbeitet User Message durch LangGraph Workflow
        
        Args:
            session_id: Session ID
            user_message: User input
            
        Returns:
            Updated ChatState
            
        Raises:
            ValueError: Wenn Session nicht existiert
        """
        
        if self.workflow is None:
            await self.initialize()
        
        # Get or create session
        state = self.get_session(session_id)
        if state is None:
            self.create_session(session_id)
            state = self.get_session(session_id)
        
        try:
            logger.info("Processing message through workflow", 
                       session_id=session_id,
                       message_length=len(user_message))
            
            # Set user message and processing flag
            state.last_user_message = user_message
            state.processing = True
            
            # Run through workflow
            result = await self.workflow.ainvoke(state)
            
            # Update session with result
            updated_state = ChatState(**result)
            updated_state.session_id = session_id  # Ensure session_id is preserved
            
            self.update_session(session_id, updated_state)
            
            logger.info("Message processed successfully", 
                       session_id=session_id,
                       total_messages=updated_state.total_messages)
            
            return updated_state
            
        except Exception as e:
            logger.error("Error processing message", 
                        session_id=session_id,
                        error=str(e))
            
            # Reset processing flag on error
            state.processing = False
            self.update_session(session_id, state)
            
            raise
    
    async def initialize_session(self, session_id: str) -> ChatState:
        """
        Initialisiert Session mit Welcome Message durch Start Node
        
        Args:
            session_id: Session ID
            
        Returns:
            Initialized ChatState mit Welcome Message
        """
        
        if self.workflow is None:
            await self.initialize()
        
        # Get or create session
        state = self.get_session(session_id)
        if state is None:
            self.create_session(session_id)
            state = self.get_session(session_id)
        
        try:
            logger.info("Initializing session", session_id=session_id)
            
            # Run start node only
            result = await self.workflow.ainvoke(state)
            
            # Update session with result
            updated_state = ChatState(**result)
            updated_state.session_id = session_id
            
            self.update_session(session_id, updated_state)
            
            logger.info("Session initialized successfully", 
                       session_id=session_id,
                       message_count=len(updated_state.messages))
            
            return updated_state
            
        except Exception as e:
            logger.error("Error initializing session", 
                        session_id=session_id,
                        error=str(e))
            raise
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Holt Session Information (ohne sensitive Daten)
        
        Args:
            session_id: Session ID
            
        Returns:
            Session info dict oder None
        """
        
        state = self.get_session(session_id)
        if state is None:
            return None
        
        return {
            "session_id": session_id,
            "active": state.active,
            "message_count": state.total_messages,
            "created_at": state.created_at.isoformat(),
            "last_updated": state.last_updated.isoformat(),
            "processing": state.processing
        }
    
    def get_all_sessions(self) -> Dict[str, Dict[str, Any]]:
        """
        Holt Übersicht aller Sessions
        
        Returns:
            Dict mit Session IDs und deren Info
        """
        
        return {
            session_id: self.get_session_info(session_id)
            for session_id in self.active_sessions.keys()
        }
    
    def cleanup_inactive_sessions(self, max_age_hours: int = 24) -> int:
        """
        Räumt alte/inactive Sessions auf
        
        Args:
            max_age_hours: Maximales Alter in Stunden
            
        Returns:
            Anzahl gelöschter Sessions
        """
        
        from datetime import timedelta
        
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        sessions_to_delete = []
        
        for session_id, state in self.active_sessions.items():
            if state.last_updated < cutoff_time or not state.active:
                sessions_to_delete.append(session_id)
        
        deleted_count = 0
        for session_id in sessions_to_delete:
            if self.delete_session(session_id):
                deleted_count += 1
        
        if deleted_count > 0:
            logger.info("Cleaned up inactive sessions", 
                       deleted_count=deleted_count,
                       max_age_hours=max_age_hours)
        
        return deleted_count


# Global Session Manager Instance
_session_manager: Optional[SessionManager] = None


async def get_session_manager() -> SessionManager:
    """
    Singleton Getter für Session Manager
    
    Returns:
        Initialized SessionManager instance
    """
    global _session_manager
    
    if _session_manager is None:
        _session_manager = SessionManager()
        await _session_manager.initialize()
    
    return _session_manager 