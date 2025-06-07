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


@router.post("/message", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """
    Non-streaming Chat Endpoint
    Für einfache Request/Response Communication
    """
    
    try:
        session_manager = await get_session_manager()
        
        # Get or create session
        session_id = request.session_id
        if not session_id:
            session_id = session_manager.create_session()
            # Initialize session if new
            await session_manager.initialize_session(session_id)
        
        logger.info("Processing chat message", 
                   session_id=session_id,
                   message_length=len(request.message))
        
        # Process message through workflow
        updated_state = await session_manager.process_message(
            session_id, 
            request.message
        )
        
        # Get the latest AI response
        ai_messages = [msg for msg in updated_state.messages if msg.type == "ai"]
        if not ai_messages:
            raise HTTPException(status_code=500, detail="No AI response generated")
        
        latest_response = ai_messages[-1]
        
        return ChatResponse(
            session_id=session_id,
            message=latest_response,
            status="success"
        )
        
    except LLMServiceException as e:
        logger.error("LLM service error in chat", error=e.to_dict())
        raise HTTPException(
            status_code=500,
            detail=f"Chat processing failed: {e.message}"
        )
    except Exception as e:
        logger.error("Unexpected error in chat", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )


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
                await session_manager.initialize_session(new_session_id)
                logger.info("📝 Created new session", session_id=new_session_id)
            else:
                new_session_id = session_id
                # Ensure session exists
                if not session_manager.get_session(new_session_id):
                    session_manager.create_session(new_session_id)
                    await session_manager.initialize_session(new_session_id)
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
            
            # Add user message to state
            state.last_user_message = message
            state.processing = True
            session_manager.update_session(new_session_id, state)
            
            # Send user message confirmation
            user_msg_data = {
                "type": "user_message",
                "content": message,
                "session_id": new_session_id
            }
            yield f"data: {json.dumps(user_msg_data)}\n\n"
            
            # Get LangChain LLM service for streaming (mit LangSmith tracing)
            from ..services import get_langchain_llm_service
            llm_service = get_langchain_llm_service()
            
            # Add user message to state (wird dann vom generic_chat_node verarbeitet)
            # WICHTIG: Nicht doppelt hinzufügen - der Node macht das
            from ..models import create_human_message
            if not state.messages or state.messages[-1].content != message:
                user_message = create_human_message(message)
                state.add_message(user_message)
            
            # Prepare messages for LLM
            recent_messages = state.get_recent_messages(limit=10)
            
            # Stream AI response
            complete_response = ""
            chunk_count = 0
            
            async for chunk in llm_service.stream_completion(
                messages=recent_messages,
                session_id=new_session_id,  # Session-Tracing für LangSmith
                temperature=0.7,
                max_tokens=1500
            ):
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
                
                # Small delay to prevent overwhelming
                await asyncio.sleep(0.01)
            
            # Add complete AI response to state
            from ..models import create_ai_message
            ai_response = create_ai_message(
                complete_response,
                metadata={
                    "streaming": True,
                    "chunk_count": chunk_count,
                    "model": llm_service.config.llm_default
                }
            )
            state.add_message(ai_response)
            state.processing = False
            session_manager.update_session(new_session_id, state)
            
            # Send completion signal
            completion_data = {
                "type": "completion",
                "session_id": new_session_id,
                "total_chunks": chunk_count,
                "message_count": state.total_messages,
                "complete_response": complete_response
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
        await session_manager.initialize_session(session_id)
        
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