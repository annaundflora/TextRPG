"""
TextRPG LangChain LLM Service
LangChain-based OpenRouter Integration für vollständiges LangSmith Tracing
"""

import time
from typing import List, Optional, Dict, Any, AsyncGenerator, Union
import structlog
from datetime import datetime
import uuid

from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.outputs import LLMResult
from langchain_core.tracers import LangChainTracer

from ..config import Settings, settings
from ..models import ChatMessage, create_ai_message, messages_to_langchain, pydantic_to_langchain
from .exceptions import (
    LLMServiceException,
    APIKeyInvalidException,
    create_llm_exception,
    LLMErrorType
)

logger = structlog.get_logger()


class SessionTracker:
    """Manages session-level tracing for LangSmith"""
    
    def __init__(self):
        self.session_runs: Dict[str, str] = {}  # session_id -> parent_run_id
    
    def get_or_create_session_run(self, session_id: str) -> str:
        """Get or create a parent run ID for the session"""
        if session_id not in self.session_runs:
            # Create a new parent run ID for this session
            parent_run_id = str(uuid.uuid4())
            self.session_runs[session_id] = parent_run_id
            logger.info("Created session run", session_id=session_id, parent_run_id=parent_run_id)
        return self.session_runs[session_id]
    
    def end_session_run(self, session_id: str):
        """Remove session run when session ends"""
        if session_id in self.session_runs:
            logger.info("Ended session run", session_id=session_id, 
                       parent_run_id=self.session_runs[session_id])
            del self.session_runs[session_id]


class LangChainLLMService:
    """
    LangChain-basierter LLM Service mit vollständigem LangSmith Tracing
    Verwendet ChatOpenAI Komponenten für automatisches Tracing
    """
    
    def __init__(self, config: Settings):
        """
        Initialisiert LangChain LLM Service
        
        Args:
            config: Application Settings
        """
        self.config = config
        self._initialized = False
        self.session_tracker = SessionTracker()
        
        # Base configuration für alle LLM instances
        self.base_config = {
            "base_url": "https://openrouter.ai/api/v1",
            "api_key": self.config.openrouter_api_key,
            "temperature": 0.7,
            "max_tokens": 2000,
            "top_p": 0.9,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
            "timeout": 30.0,
            "max_retries": 2,
            # LangSmith tracing wird automatisch aktiviert über env vars
        }
        
        # LLM instances (werden lazy initialisiert)
        self._default_llm: Optional[ChatOpenAI] = None
        self._creator_llm: Optional[ChatOpenAI] = None
        self._gamemaster_llm: Optional[ChatOpenAI] = None
    
    def initialize(self) -> None:
        """
        Initialisiert den Service (nur einmal ausgeführt)
        """
        if self._initialized:
            return
        
        try:
            # Validate API key
            if not self.config.openrouter_api_key:
                raise APIKeyInvalidException("OpenRouter API key not configured")
            
            # Log LangSmith configuration
            if self.config.langsmith_tracing:
                logger.info("LangSmith tracing enabled", 
                           project=self.config.langsmith_project,
                           endpoint=self.config.langsmith_endpoint)
            
            self._initialized = True
            logger.info("LangChain LLM Service initialized successfully",
                       langsmith_tracing=self.config.langsmith_tracing,
                       langsmith_project=self.config.langsmith_project,
                       langsmith_endpoint=self.config.langsmith_endpoint,
                       has_api_key=bool(self.config.langsmith_api_key))
            
        except Exception as e:
            logger.error("LangChain LLM Service initialization failed", error=str(e))
            raise LLMServiceException(f"Service initialization failed: {str(e)}")
    
    def get_default_llm(self) -> ChatOpenAI:
        """Lazy getter für Default LLM"""
        if self._default_llm is None:
            self._default_llm = ChatOpenAI(
                model=self.config.llm_default,
                **self.base_config
            )
        return self._default_llm
    
    def get_creator_llm(self) -> ChatOpenAI:
        """Lazy getter für Story Creator LLM"""
        if self._creator_llm is None:
            self._creator_llm = ChatOpenAI(
                model=self.config.llm_creator,
                **self.base_config
            )
        return self._creator_llm
    
    def get_gamemaster_llm(self) -> ChatOpenAI:
        """Lazy getter für Gamemaster LLM"""
        if self._gamemaster_llm is None:
            self._gamemaster_llm = ChatOpenAI(
                model=self.config.llm_gamemaster,
                **self.base_config
            )
        return self._gamemaster_llm
    
    def get_llm_by_name(self, model_name: Optional[str] = None) -> ChatOpenAI:
        """
        Gibt LLM Instance basierend auf Model-Name zurück
        
        Args:
            model_name: Model name oder None für default
            
        Returns:
            ChatOpenAI instance
        """
        if not model_name:
            return self.get_default_llm()
        elif model_name == self.config.llm_creator:
            return self.get_creator_llm()
        elif model_name == self.config.llm_gamemaster:
            return self.get_gamemaster_llm()
        else:
            # Create custom LLM for specific model
            return ChatOpenAI(model=model_name, **self.base_config)
    
    def _convert_messages_to_langchain(self, messages: List[ChatMessage]) -> List[BaseMessage]:
        """
        Konvertiert ChatMessage Liste zu LangChain BaseMessage Liste
        
        Args:
            messages: List of ChatMessage objects
            
        Returns:
            List of LangChain BaseMessage objects
        """
        langchain_messages = []
        
        for msg in messages:
            if msg.type == "human":
                langchain_messages.append(HumanMessage(content=msg.content))
            elif msg.type == "ai":
                langchain_messages.append(AIMessage(content=msg.content))
            elif msg.type == "system":
                langchain_messages.append(SystemMessage(content=msg.content))
            else:
                logger.warning("Unknown message type", msg_type=msg.type)
                # Fallback to HumanMessage
                langchain_messages.append(HumanMessage(content=msg.content))
        
        return langchain_messages
    
    def _convert_response_to_chatmessage(
        self, 
        response: AIMessage, 
        model_name: str,
        response_metadata: Optional[Dict] = None
    ) -> ChatMessage:
        """
        Konvertiert LangChain AIMessage zu ChatMessage
        
        Args:
            response: LangChain AIMessage
            model_name: Name des verwendeten Models
            response_metadata: Additional metadata
            
        Returns:
            ChatMessage instance
        """
        metadata = {
            "model": model_name,
            "langchain_response": True,
            **getattr(response, 'response_metadata', {}),
            **(response_metadata or {})
        }
        
        return create_ai_message(response.content, metadata)
    
    async def chat_completion(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        session_id: Optional[str] = None,
        **kwargs
    ) -> ChatMessage:
        """
        Async Chat Completion mit LangChain und Session-Tracing
        
        Args:
            messages: Chat message history
            model: Model name (optional)
            session_id: Session ID for tracing grouping
            **kwargs: Additional model parameters
            
        Returns:
            AI response as ChatMessage
            
        Raises:
            LLMServiceException: Bei Fehlern
        """
        
        if not self._initialized:
            self.initialize()
        
        start_time = time.time()
        
        try:
            # Get appropriate LLM
            llm = self.get_llm_by_name(model)
            model_name = model or self.config.llm_default
            
            # Convert messages to LangChain format
            langchain_messages = self._convert_messages_to_langchain(messages)
            
            # Setup session tracing if session_id provided
            config = {}
            if session_id and self.config.langsmith_tracing:
                parent_run_id = self.session_tracker.get_or_create_session_run(session_id)
                config = {
                    "tags": [f"session:{session_id}", "chat_completion"],
                    "metadata": {
                        "session_id": session_id,
                        "message_count": len(messages),
                        "model": model_name
                    }
                }
            
            logger.info("Starting LangChain chat completion", 
                       model=model_name,
                       message_count=len(messages),
                       session_id=session_id,
                       langsmith_tracing=bool(session_id and self.config.langsmith_tracing))
            
            # Apply additional parameters
            if kwargs:
                # Create new LLM instance with updated parameters
                updated_config = {**self.base_config, **kwargs}
                llm = ChatOpenAI(model=model_name, **updated_config)
            
            # Invoke LLM with session tracing (this will be traced by LangSmith)
            if config:
                response = await llm.ainvoke(langchain_messages, config=config)
            else:
                response = await llm.ainvoke(langchain_messages)
            
            # Convert response
            result = self._convert_response_to_chatmessage(
                response, 
                model_name,
                {
                    "completion_time": time.time() - start_time,
                    "session_id": session_id
                }
            )
            
            duration = time.time() - start_time
            logger.info("LangChain chat completion successful", 
                       duration=duration,
                       model=model_name,
                       response_length=len(result.content),
                       session_id=session_id)
            
            return result
            
        except Exception as e:
            context = {
                "model_name": model or self.config.llm_default,
                "duration": time.time() - start_time,
                "langchain_error": True,
                "session_id": session_id
            }
            logger.error("LangChain chat completion failed", 
                        error=str(e), 
                        context=context)
            raise create_llm_exception(e, context)
    
    async def stream_completion(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        session_id: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Streaming Chat Completion mit LangChain und Session-Tracing
        
        Args:
            messages: Chat message history
            model: Model name (optional)
            session_id: Session ID for tracing grouping
            **kwargs: Additional model parameters
            
        Yields:
            Content chunks as strings
            
        Raises:
            LLMServiceException: Bei Fehlern
        """
        
        if not self._initialized:
            self.initialize()
        
        start_time = time.time()
        
        try:
            # Get appropriate LLM
            llm = self.get_llm_by_name(model)
            model_name = model or self.config.llm_default
            
            # Convert messages to LangChain format
            langchain_messages = self._convert_messages_to_langchain(messages)
            
            # Setup session tracing if session_id provided
            config = {}
            if session_id and self.config.langsmith_tracing:
                parent_run_id = self.session_tracker.get_or_create_session_run(session_id)
                config = {
                    "tags": [f"session:{session_id}", "streaming_completion"],
                    "metadata": {
                        "session_id": session_id,
                        "message_count": len(messages),
                        "model": model_name,
                        "streaming": True
                    }
                }
            
            logger.info("Starting LangChain streaming completion", 
                       model=model_name,
                       message_count=len(messages),
                       session_id=session_id)
            
            # Apply additional parameters
            if kwargs:
                # Create new LLM instance with updated parameters
                updated_config = {**self.base_config, **kwargs}
                llm = ChatOpenAI(model=model_name, **updated_config)
            
            # Stream response with session tracing
            chunk_count = 0
            async for chunk in llm.astream(langchain_messages, config=config if config else None):
                if chunk.content:
                    chunk_count += 1
                    yield chunk.content
            
            duration = time.time() - start_time
            logger.info("LangChain streaming completion successful", 
                       duration=duration,
                       model=model_name,
                       chunk_count=chunk_count,
                       session_id=session_id)
            
        except Exception as e:
            context = {
                "model_name": model or self.config.llm_default,
                "duration": time.time() - start_time,
                "langchain_streaming_error": True,
                "session_id": session_id
            }
            logger.error("LangChain streaming completion failed", 
                        error=str(e), 
                        context=context)
            raise create_llm_exception(e, context)
    
    def end_session(self, session_id: str):
        """
        End session tracing
        
        Args:
            session_id: Session ID to end
        """
        self.session_tracker.end_session_run(session_id)


# Global Service Instance
_langchain_llm_service: Optional[LangChainLLMService] = None


def get_langchain_llm_service() -> LangChainLLMService:
    """
    Singleton Getter für LangChain LLM Service
    
    Returns:
        LangChainLLMService instance
    """
    global _langchain_llm_service
    
    if _langchain_llm_service is None:
        _langchain_llm_service = LangChainLLMService(settings)
        _langchain_llm_service.initialize()
    
    return _langchain_llm_service


async def close_langchain_llm_service():
    """
    Cleanup für LangChain LLM Service
    """
    global _langchain_llm_service
    
    if _langchain_llm_service is not None:
        logger.info("Closing LangChain LLM Service")
        _langchain_llm_service = None 