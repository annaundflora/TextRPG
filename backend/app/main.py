"""
TextRPG Backend - Phase 1 Foundation Chatbot
FastAPI Server mit SSE Streaming Support
"""

import os
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .utils import get_startup_info
from .services import close_llm_service

# Explizit Environment Variables für LangSmith setzen BEVOR LangChain importiert wird
if settings.langsmith_tracing:
    os.environ["LANGSMITH_TRACING"] = str(settings.langsmith_tracing).lower()
    
if settings.langsmith_api_key:
    os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
    
os.environ["LANGSMITH_ENDPOINT"] = settings.langsmith_endpoint  
os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project

# Configure structured logging
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(20),  # INFO level
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Log LangSmith Konfiguration
logger.info("LangSmith configuration loaded",
           tracing_enabled=settings.langsmith_tracing,
           project=settings.langsmith_project,
           endpoint=settings.langsmith_endpoint)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("TextRPG Backend starting up...")
    
    # Startup Validation
    try:
        startup_info = get_startup_info()
        logger.info("Startup validation completed", **startup_info)
        
        if not startup_info["ready_for_startup"]:
            logger.warning("Configuration issues detected", 
                          config_errors=startup_info["configuration"]["errors"],
                          env_issues=startup_info["environment"]["issues"])
    except Exception as e:
        logger.error("Startup validation failed", error=str(e))
    
    yield
    
    # Cleanup
    logger.info("TextRPG Backend shutting down...")
    try:
        await close_llm_service()
        logger.info("LLM Service closed")
    except Exception as e:
        logger.error("Error during shutdown", error=str(e))


# FastAPI App Instance
app = FastAPI(
    title="TextRPG Backend",
    description="Generatives TextRPG mit AI-Agenten - Phase 1 Foundation",
    version="1.0.0-phase1"
)

# CORS Configuration für Development
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "TextRPG Backend - Phase 1 Foundation", 
        "status": "running",
        "version": "1.0.0-phase1"
    }


@app.get("/health")
async def health_check():
    """Detailed health check with CORS headers"""
    logger.info("🏥 Health check requested")
    
    return {
        "status": "healthy",
        "phase": "1 - Foundation Chatbot",
        "features": [
            "Basic FastAPI Setup",
            "CORS Configuration", 
            "Structured Logging",
            "Pydantic Settings Management",
            "Ready for LangGraph Integration"
        ],
        "config": {
            "debug": settings.debug,
            "log_level": settings.log_level,
            "llm_default": settings.llm_default,
            "cors_origins": settings.cors_origins
        },
        "timestamp": logger.info("✅ Health check completed")
    }


# Test LLM Service Integration für Phase 1
from .services import get_langchain_llm_service, LLMServiceException
from .models import create_human_message
from .graph import get_session_manager
from .routes import chat_router

# Include chat routes
app.include_router(chat_router)

@app.get("/test-llm")
async def test_llm_service():
    """Test endpoint für LangChain LLM Service Integration mit LangSmith Tracing"""
    try:
        llm_service = get_langchain_llm_service()
        
        # Simple test message
        test_messages = [
            create_human_message("Hallo! Kannst du mir in einem Satz erklären, was ein TextRPG ist?")
        ]
        
        # Test chat completion
        response = await llm_service.chat_completion(test_messages)
        
        return {
            "status": "success",
            "test": "LangChain LLM Service Integration",
            "model_used": response.metadata.get("model", "unknown"),
            "response": response.content,
            "response_length": len(response.content),
            "metadata": response.metadata,
            "langchain_service": True,
            "langsmith_tracing": True
        }
        
    except LLMServiceException as e:
        logger.error("LLM Service test failed", error=e.to_dict())
        return {
            "status": "error", 
            "test": "LangChain LLM Service Integration",
            "error_type": e.error_type.value,
            "error_message": e.message,
            "recoverable": e.recoverable,
            "langchain_service": True
        }
    except Exception as e:
        logger.error("Unexpected error in LLM test", error=str(e))
        return {
            "status": "error",
            "test": "LangChain LLM Service Integration", 
            "error_message": f"Unexpected error: {str(e)}",
            "langchain_service": True
        }


@app.get("/test-workflow")
async def test_workflow():
    """
    Test endpoint für LangGraph Workflow Integration
    DISABLED: Referenziert gelöschte Session Manager Methoden
    """
    return {
        "status": "disabled",
        "test": "LangGraph Workflow Integration", 
        "message": "This endpoint is disabled as it references removed session manager methods",
        "recommendation": "Use /chat/stream endpoint for testing workflow"
    }


@app.get("/sessions")
async def get_all_sessions():
    """Get overview of all active sessions"""
    try:
        session_manager = await get_session_manager()
        sessions = session_manager.get_all_sessions()
        
        return {
            "status": "success",
            "total_sessions": len(sessions),
            "sessions": sessions
        }
        
    except Exception as e:
        logger.error("Failed to get sessions", error=str(e))
        return {
            "status": "error",
            "error_message": str(e)
        }

# Route imports will be added in subsequent tasks
# from app.routes import chat

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.reload,
        log_level=settings.log_level
    ) 