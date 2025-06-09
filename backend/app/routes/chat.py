"""
TextRPG Chat Routes
FastAPI Endpoints für Chat Communication mit SSE Streaming
"""

import json
import asyncio
from typing import Optional, AsyncGenerator
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
import structlog

from ..models import ChatRequest, ChatResponse, ChatMessage, StreamingResponse as StreamingResponseModel
from ..graph import get_session_manager
from ..services import LLMServiceException

logger = structlog.get_logger()

router = APIRouter(prefix="/chat", tags=["chat"])


@router.get("/stream")
async def stream_chat(
    message: str = Query(..., description="User message to process"),
    session_id: Optional[str] = Query(None, description="Session ID (auto-generated if not provided)")
):
    """
    Server-Sent Events Streaming Chat Endpoint
    Streams AI response in real-time chunks
    """
    
    logger.info("🚀 SSE Endpoint called", 
               message_preview=message[:50] + "..." if len(message) > 50 else message,
               session_id=session_id)
    
    async def generate_sse_stream() -> AsyncGenerator[str, None]:
        """Generate SSE formatted stream"""
        
        try:
            logger.info("🔧 Starting SSE stream generation")
            session_manager = await get_session_manager()
            
            # Get or create session
            if not session_id:
                new_session_id = session_manager.create_session()
                logger.info("📝 Created new session", session_id=new_session_id)
            else:
                new_session_id = session_id
                # Ensure session exists
                if not session_manager.get_session(new_session_id):
                    session_manager.create_session(new_session_id)
                    logger.info("🔄 Recreated missing session", session_id=new_session_id)
                else:
                    logger.info("✅ Using existing session", session_id=new_session_id)
            
            logger.info("🎯 Processing message", 
                       session_id=new_session_id,
                       message_length=len(message))
            
            # Send session info first
            session_info = {
                "type": "session_info",
                "session_id": new_session_id,
                "timestamp": session_manager.get_session_info(new_session_id)
            }
            
            session_info_data = f"data: {json.dumps(session_info)}\n\n"
            logger.debug("📤 Sending session info", data_length=len(session_info_data))
            yield session_info_data
            
            # Get current state
            state = session_manager.get_session(new_session_id)
            if not state:
                raise ValueError("Session not found")
            
            # Send user message confirmation first
            user_msg_data = {
                "type": "user_message",
                "content": message,
                "session_id": new_session_id
            }
            yield f"data: {json.dumps(user_msg_data)}\n\n"
            
            # Process via Agent-Workflow with streaming
            complete_response = ""
            chunk_count = 0
            
            # Use SessionManager's stream_process_message 
            async for chunk in session_manager.stream_process_message(new_session_id, message):
                complete_response += chunk
                chunk_count += 1
                
                # Send chunk data
                chunk_data = {
                    "type": "ai_chunk",
                    "content": chunk,
                    "chunk_id": chunk_count,
                    "session_id": new_session_id,
                    "is_final": False
                }
                
                yield f"data: {json.dumps(chunk_data)}\n\n"
                
                # Reduced delay for faster streaming (was 0.01)
                await asyncio.sleep(0.001)
            
            # Get updated session state for metadata
            updated_state = session_manager.get_session(new_session_id)
            
            # Send completion signal with agent metadata
            completion_data = {
                "type": "completion",
                "session_id": new_session_id,
                "total_chunks": chunk_count,
                "message_count": len(updated_state.messages) if updated_state else 0,
                "complete_response": complete_response,
                "agent": updated_state.current_agent if updated_state else None
            }
            
            yield f"data: {json.dumps(completion_data)}\n\n"
            
            # Send final SSE termination
            yield "data: [DONE]\n\n"
            
            logger.info("SSE stream completed", 
                       session_id=new_session_id,
                       chunk_count=chunk_count,
                       response_length=len(complete_response))
            
        except LLMServiceException as e:
            logger.error("LLM service error in SSE stream", error=e.to_dict())
            
            error_data = {
                "type": "error",
                "error_type": e.error_type.value,
                "error_message": e.message,
                "recoverable": e.recoverable,
                "session_id": session_id or "unknown"
            }
            
            yield f"data: {json.dumps(error_data)}\n\n"
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            logger.error("Unexpected error in SSE stream", error=str(e))
            
            error_data = {
                "type": "error",
                "error_type": "unexpected_error",
                "error_message": str(e),
                "recoverable": False,
                "session_id": session_id or "unknown"
            }
            
            yield f"data: {json.dumps(error_data)}\n\n"
            yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        generate_sse_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
            "Access-Control-Allow-Origin": "*"  # Allow CORS for SSE
        }
    )


@router.get("/session/{session_id}")
async def get_session(session_id: str):
    """
    Get session information and message history
    """
    
    try:
        session_manager = await get_session_manager()
        
        state = session_manager.get_session(session_id)
        if not state:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {
            "session_id": session_id,
            "session_info": session_manager.get_session_info(session_id),
            "messages": [
                {
                    "id": msg.id,
                    "type": msg.type,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "metadata": msg.metadata
                }
                for msg in state.messages
            ]
        }
        
    except Exception as e:
        logger.error("Error getting session", session_id=session_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/session")
async def create_session():
    """
    Create new chat session
    """
    
    try:
        session_manager = await get_session_manager()
        
        session_id = session_manager.create_session()
        
        return {
            "session_id": session_id,
            "session_info": session_manager.get_session_info(session_id),
            "status": "created"
        }
        
    except Exception as e:
        logger.error("Error creating session", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """
    Delete chat session
    """
    
    try:
        session_manager = await get_session_manager()
        
        if session_manager.delete_session(session_id):
            return {"status": "deleted", "session_id": session_id}
        else:
            raise HTTPException(status_code=404, detail="Session not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting session", session_id=session_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions")
async def list_sessions():
    """
    List all active sessions
    """
    
    try:
        session_manager = await get_session_manager()
        sessions = session_manager.get_all_sessions()
        
        return {
            "total_sessions": len(sessions),
            "sessions": sessions
        }
        
    except Exception as e:
        logger.error("Error listing sessions", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) 