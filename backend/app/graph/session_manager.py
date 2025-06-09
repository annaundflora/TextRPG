"""
TextRPG Session Manager - Command Pattern Migration
Verwaltet Chat Sessions für Command-basierte LangGraph Workflows
"""

from typing import Dict, Optional, Any, AsyncGenerator
import structlog
from datetime import datetime, timedelta
import uuid
import asyncio

from ..models import ChatState, ChatMessage, create_human_message
from .workflow import get_workflow

logger = structlog.get_logger()


class SessionManager:
    """
    Verwaltet aktive Chat Sessions und deren State
    Command Pattern Migration - Vereinfachtes Session Management
    """
    
    def __init__(self):
        """Initialisiert Session Manager"""
        self.active_sessions: Dict[str, ChatState] = {}
        self.workflow = None
    
    async def initialize(self) -> None:
        """Initialisiert Command Pattern Workflow"""
        if self.workflow is None:
            self.workflow = get_workflow()
            logger.info("Session Manager initialized with Command Pattern Workflow")
    
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
        
        # Create initial state für Command Pattern
        state = ChatState(
            session_id=session_id,
            messages=[],
            active=True,
            created_at=datetime.utcnow(),
            last_updated=datetime.utcnow(),
            processing=False,
            current_agent=None
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
    
    async def stream_process_message(
        self,
        session_id: str,
        user_message: str
    ) -> AsyncGenerator[str, None]:
        """
        Verarbeitet eine User-Message und streamt die AI-Response.
        Nutzt LangGraph für Agent-Transitions via Commands.
        
        Args:
            session_id: Session ID
            user_message: User input
            
        Yields:
            Streamed response chunks (optimized for performance)
        """
        state = self.get_session(session_id)
        if not state:
            yield "Session nicht gefunden."
            return
        
        try:
            state.processing = True
            self.update_session(session_id, state)
            
            logger.info("Starting LangGraph workflow with Command support",
                       session_id=session_id,
                       message_preview=user_message[:50])
            
            # Füge User-Message hinzu
            user_msg = create_human_message(user_message)
            state.messages.append(user_msg)
            
            # Bereite State für LangGraph vor
            graph_state = {
                "session_id": state.session_id,
                "messages": state.messages,
                "story_phase": state.story_phase,
                "current_agent": state.current_agent,
                "handoff_data": state.handoff_data,
                "chapter_count": state.chapter_count,
                "interaction_count": state.interaction_count,
                "active": state.active,
                "processing": state.processing,
                "created_at": state.created_at,
                "last_updated": state.last_updated,
                "end_trigger": state.end_trigger
            }
            
            # LangGraph Workflow ausführen
            result = await self.workflow.ainvoke(graph_state)
            
            logger.info(f"LangGraph workflow completed. Final state keys: {list(result.keys())}")
            
            # Extract und stream die Response
            updated_messages = result.get("messages", [])
            if updated_messages and len(updated_messages) > len(state.messages):
                # Neue Messages wurden hinzugefügt
                for new_message in updated_messages[len(state.messages):]:
                    # Handle both ChatMessage and LangChain AIMessage objects
                    if hasattr(new_message, 'type') and new_message.type == "ai":
                        response_text = new_message.content
                        logger.info(f"Using ChatMessage content: {response_text[:50]}...", session_id=session_id)
                    elif hasattr(new_message, 'content'):
                        # LangChain AIMessage object
                        response_text = str(new_message.content)
                        logger.info(f"Converting LangChain object to string: {type(new_message)}", session_id=session_id)
                    else:
                        response_text = str(new_message)
                        logger.error(f"Unknown message format, converting to string: {type(new_message)}", session_id=session_id)
                    
                    # Ensure response_text is actually a string
                    if not isinstance(response_text, str):
                        response_text = str(response_text)
                        logger.warning(f"Response was not a string, converted: {type(response_text)}", session_id=session_id)
                    
                    # OPTIMIZED STREAMING: Chunk text into word groups instead of single characters
                    words = response_text.split(' ')
                    current_chunk = ""
                    
                    for i, word in enumerate(words):
                        current_chunk += word
                        
                        # Add space except for last word
                        if i < len(words) - 1:
                            current_chunk += " "
                        
                        # Send chunks of 3-5 words for natural reading flow
                        if len(current_chunk.split()) >= 4 or i == len(words) - 1:
                            if current_chunk.strip():  # Only yield non-empty chunks
                                yield current_chunk
                                await asyncio.sleep(0.05)  # Much faster: 20 chunks per second
                                current_chunk = ""
            else:
                response_text = "Keine Antwort erhalten."
                yield response_text
            
            # Update session state mit LangGraph Result
            state.messages = updated_messages
            
            # Update andere State-Felder
            if "handoff_data" in result:
                state.handoff_data = result["handoff_data"]
            if "chapter_count" in result:
                state.chapter_count = result["chapter_count"]
            if "interaction_count" in result:
                state.interaction_count = result["interaction_count"]
            if "current_agent" in result:
                state.current_agent = result["current_agent"]
            if "story_phase" in result:
                state.story_phase = result["story_phase"]
            
            state.processing = False
            self.update_session(session_id, state)
            
            logger.info("LangGraph workflow streaming completed", 
                       session_id=session_id)

        except Exception as e:
            logger.error("Error in LangGraph workflow processing", 
                         session_id=session_id,
                         error=str(e),
                         exc_info=True)
            yield f"\n\nEin Fehler ist aufgetreten: {str(e)}"
        
        finally:
            # Ensure session is not stuck in processing
            if state:
                state.processing = False
                self.update_session(session_id, state)
            
            logger.info("LangGraph workflow stream context finished.", 
                       session_id=session_id)
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Gibt detaillierte Informationen über eine Session zurück.
        
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
            "message_count": len(state.messages),
            "created_at": state.created_at.isoformat(),
            "last_updated": state.last_updated.isoformat(),
            "processing": state.processing,
            "current_agent": state.current_agent
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