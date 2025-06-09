"""
TextRPG Session Manager
Verwaltet Chat Sessions und LangGraph State
"""

from typing import Dict, Optional, Any, AsyncGenerator
import structlog
from datetime import datetime
import uuid
import asyncio

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
            self.workflow = get_workflow()  # Use simplified Agent Workflow
            logger.info("Session Manager initialized with simplified Agent Workflow")
    
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
        
        # Create initial state - simplified for MVP
        state = ChatState(
            session_id=session_id,
            messages=[],
            active=True,
            created_at=datetime.utcnow(),
            last_updated=datetime.utcnow(),
            processing=False,
            current_agent=None,
            last_user_message=""
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
        Verarbeitet User Message durch LangGraph Workflow mit echtem Token-Streaming
        
        Args:
            session_id: Session ID
            user_message: User input
            
        Yields:
            AI response tokens in real-time
            
        Raises:
            ValueError: Wenn Session nicht existiert
        """
        
        if self.workflow is None:
            await self.initialize()

        state = self.get_session(session_id)
        if state is None:
            logger.warning("Session not found, creating new one.", session_id=session_id)
            self.create_session(session_id)
            state = self.get_session(session_id)

        complete_response = ""
        tokens_streamed = 0
        
        try:
            logger.info("Streaming message through workflow", 
                       session_id=session_id,
                       message_length=len(user_message))

            if not state.messages or state.messages[-1].content != user_message:
                user_msg = create_human_message(user_message)
                state.add_message(user_msg)
            
            state.last_user_message = user_message
            state.processing = True
            self.update_session(session_id, state)
            
            final_state_from_event = None
            
            async for event in self.workflow.astream_events(state, version="v1"):
                kind = event["event"]
                
                if kind == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    if hasattr(chunk, 'content') and chunk.content:
                        token = chunk.content
                        complete_response += token
                        tokens_streamed += 1
                        yield token
                        if tokens_streamed % 5 == 0:
                            await asyncio.sleep(0.01)
                
                elif kind == "on_chain_end":
                    if event["name"] == "LangGraph":
                        final_state_from_event = event["data"].get("output")
                        logger.debug("LangGraph final state received from events", session_id=session_id)

            final_chat_state = state 
            if final_state_from_event:
                if isinstance(final_state_from_event, dict):
                    # Extract state from nested structure
                    state_dict = None
                    
                    # Check if state is nested under agent name (e.g., {'story_creator': {...}})
                    if len(final_state_from_event) == 1:
                        agent_key = list(final_state_from_event.keys())[0]
                        nested_value = final_state_from_event[agent_key]
                        if isinstance(nested_value, dict) and 'messages' in nested_value:
                            state_dict = nested_value
                            logger.debug(f"Extracted state from nested structure under '{agent_key}'", 
                                       session_id=session_id)
                    
                    # If not nested, use directly
                    if state_dict is None and 'messages' in final_state_from_event:
                        state_dict = final_state_from_event
                    
                    # Create ChatState from dict
                    if state_dict and 'messages' in state_dict:
                        try:
                            # Add required fields if missing
                            state_dict['session_id'] = session_id
                            if 'active' not in state_dict:
                                state_dict['active'] = state.active
                            if 'created_at' not in state_dict:
                                state_dict['created_at'] = state.created_at
                            
                            # Convert messages
                            from ..models import langchain_to_pydantic, ChatMessage as ChatMessageModel
                            converted_messages = []
                            for m in state_dict.get('messages', []):
                                if isinstance(m, dict):
                                    # Convert dict to ChatMessage
                                    converted_messages.append(ChatMessageModel(**m))
                                elif hasattr(m, 'content'):  # LangChain message
                                    converted_messages.append(langchain_to_pydantic(m))
                                elif isinstance(m, ChatMessageModel):
                                    converted_messages.append(m)
                                else:
                                    logger.warning(f"Unknown message type: {type(m)}", session_id=session_id)
                            
                            state_dict['messages'] = converted_messages
                            
                            final_chat_state = ChatState(**state_dict)
                            logger.info("Successfully created ChatState from workflow output", 
                                      session_id=session_id,
                                      message_count=len(final_chat_state.messages),
                                      current_agent=final_chat_state.current_agent)
                        except Exception as e:
                            logger.error("Error creating ChatState from final event state", 
                                       error=str(e), 
                                       session_id=session_id)
                    else:
                        logger.warning("Could not extract valid state from workflow output", 
                                     session_id=session_id)

                elif hasattr(final_state_from_event, '__class__') and final_state_from_event.__class__.__name__ == 'ChatState':
                    final_chat_state = final_state_from_event
            else:
                 logger.warning("No final state found in events, using original state", 
                              session_id=session_id)

            logger.info("Streaming completed, final state processed.", 
                       session_id=session_id,
                       tokens_streamed=tokens_streamed,
                       current_agent=final_chat_state.current_agent)

        except Exception as e:
            logger.error("Error in stream_process_message", 
                         session_id=session_id,
                         error=str(e),
                         exc_info=True)
            yield f"\n\nEin Fehler ist aufgetreten: {str(e)}"
        
        finally:
            # Always ensure the session is updated and not stuck in processing
            final_chat_state.processing = False
            # The AI response from the stream should be in the messages list from the final state
            # No need to add it manually if the graph nodes do their job
            self.update_session(session_id, final_chat_state)
            
            logger.info("SSE stream context finished.", 
                       session_id=session_id, 
                       response_length=len(complete_response))
    
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
            # Simplified for MVP
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