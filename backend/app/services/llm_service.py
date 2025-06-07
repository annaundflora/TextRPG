"""
TextRPG LLM Service
OpenRouter API Integration für Chat Completions
"""

import json
import time
from typing import List, Optional, Dict, Any, AsyncGenerator, Union
import httpx
import structlog
from datetime import datetime

from ..config import Settings, settings
from ..models import ChatMessage, create_ai_message, messages_to_langchain
from .exceptions import (
    LLMServiceException,
    APIKeyInvalidException,
    create_llm_exception,
    LLMErrorType
)

logger = structlog.get_logger()


class LLMService:
    """
    Service für OpenRouter API Integration
    Async Chat Completions mit Streaming Support
    """
    
    def __init__(self, config: Settings = None):
        """
        Initialisiert LLM Service mit Configuration
        
        Args:
            config: Settings instance (default: global settings)
        """
        self.config = config or settings
        self.base_url = "https://openrouter.ai/api/v1"
        self.client: Optional[httpx.AsyncClient] = None
        self._initialized = False
        
        # Default Request Parameters
        self.default_params = {
            "temperature": 0.7,
            "max_tokens": 2000,
            "top_p": 0.9,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0
        }
        
        # Request Timeouts
        self.timeout_config = httpx.Timeout(
            connect=10.0,  # Connection timeout
            read=30.0,     # Read timeout  
            write=10.0,    # Write timeout
            pool=60.0      # Pool timeout
        )
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def initialize(self) -> None:
        """
        Initialisiert HTTP Client und validiert API Key
        """
        if self._initialized:
            return
        
        try:
            # Validate API Key
            if not self.config.openrouter_api_key:
                raise APIKeyInvalidException("OPENROUTER_API_KEY nicht gesetzt")
            
            # Initialize HTTP Client
            headers = {
                "Authorization": f"Bearer {self.config.openrouter_api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://textrpg.local",  # Required by OpenRouter
                "X-Title": "TextRPG"  # Optional but recommended
            }
            
            self.client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=headers,
                timeout=self.timeout_config,
                limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
            )
            
            # Test API Key
            await self.validate_api_key()
            
            self._initialized = True
            logger.info("LLM Service initialized successfully")
            
        except Exception as e:
            logger.error("LLM Service initialization failed", error=str(e))
            if self.client:
                await self.client.aclose()
                self.client = None
            raise create_llm_exception(e)
    
    async def close(self) -> None:
        """
        Schließt HTTP Client und räumt Ressourcen auf
        """
        if self.client:
            await self.client.aclose()
            self.client = None
        self._initialized = False
        logger.info("LLM Service closed")
    
    async def validate_api_key(self) -> bool:
        """
        Validiert OpenRouter API Key durch Test-Request
        
        Returns:
            True wenn API Key gültig
            
        Raises:
            APIKeyInvalidException: Bei ungültigem API Key
        """
        try:
            # Simple test request to validate API key
            response = await self.client.get("/models")
            
            if response.status_code == 401:
                raise APIKeyInvalidException("API Key ungültig oder abgelaufen")
            elif response.status_code != 200:
                logger.warning("API Key validation unexpected status", 
                             status_code=response.status_code)
            
            logger.info("API Key validation successful")
            return True
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise APIKeyInvalidException("API Key ungültig")
            raise create_llm_exception(e)
        except Exception as e:
            raise create_llm_exception(e)
    
    def _build_request(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Baut OpenRouter API Request aus ChatMessages
        
        Args:
            messages: Chat message history
            model: Model name (default: from config)
            stream: Enable streaming response
            **kwargs: Additional parameters
            
        Returns:
            API request dictionary
        """
        
        # Convert to OpenAI format
        api_messages = []
        for msg in messages:
            api_messages.append({
                "role": "user" if msg.type == "human" else "assistant" if msg.type == "ai" else "system",
                "content": msg.content
            })
        
        # Build request
        request_data = {
            "model": model or self.config.llm_default,
            "messages": api_messages,
            "stream": stream,
            **self.default_params,
            **kwargs
        }
        
        return request_data
    
    def _handle_response(self, response_data: Dict[str, Any]) -> ChatMessage:
        """
        Konvertiert OpenRouter Response zu ChatMessage
        
        Args:
            response_data: OpenRouter API response
            
        Returns:
            ChatMessage instance
            
        Raises:
            ResponseInvalidException: Bei invalid response
        """
        try:
            choices = response_data.get("choices", [])
            if not choices:
                raise ValueError("No choices in response")
            
            choice = choices[0]
            message_data = choice.get("message", {})
            content = message_data.get("content", "")
            
            if not content:
                raise ValueError("Empty content in response")
            
            # Extract metadata
            metadata = {
                "model": response_data.get("model", "unknown"),
                "usage": response_data.get("usage", {}),
                "finish_reason": choice.get("finish_reason"),
                "response_id": response_data.get("id"),
                "created": response_data.get("created")
            }
            
            return create_ai_message(content, metadata)
            
        except Exception as e:
            logger.error("Response handling failed", error=str(e), response_data=response_data)
            raise create_llm_exception(e, {"details": "Invalid response format"})
    
    async def chat_completion(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        **kwargs
    ) -> ChatMessage:
        """
        Async Chat Completion (non-streaming)
        
        Args:
            messages: Chat message history
            model: Model name (optional)
            **kwargs: Additional model parameters
            
        Returns:
            AI response as ChatMessage
            
        Raises:
            LLMServiceException: Bei Fehlern
        """
        
        if not self._initialized:
            await self.initialize()
        
        start_time = time.time()
        
        try:
            # Build request
            request_data = self._build_request(messages, model, stream=False, **kwargs)
            
            logger.info("Starting chat completion", 
                       model=request_data["model"],
                       message_count=len(messages))
            
            # Make API call
            response = await self.client.post("/chat/completions", json=request_data)
            response.raise_for_status()
            
            # Handle response
            response_data = response.json()
            result = self._handle_response(response_data)
            
            duration = time.time() - start_time
            logger.info("Chat completion successful", 
                       duration=duration,
                       model=request_data["model"],
                       response_length=len(result.content))
            
            return result
            
        except httpx.HTTPStatusError as e:
            context = {
                "model_name": model or self.config.llm_default,
                "status_code": e.response.status_code,
                "response_text": e.response.text
            }
            raise create_llm_exception(e, context)
            
        except httpx.TimeoutException as e:
            context = {
                "timeout_seconds": self.timeout_config.read,
                "model_name": model or self.config.llm_default
            }
            raise create_llm_exception(e, context)
            
        except Exception as e:
            context = {
                "model_name": model or self.config.llm_default,
                "duration": time.time() - start_time
            }
            raise create_llm_exception(e, context)
    
    async def stream_completion(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Async Streaming Chat Completion
        
        Args:
            messages: Chat message history
            model: Model name (optional)
            **kwargs: Additional model parameters
            
        Yields:
            Content chunks as strings
            
        Raises:
            LLMServiceException: Bei Fehlern
        """
        
        if not self._initialized:
            await self.initialize()
        
        try:
            # Build request
            request_data = self._build_request(messages, model, stream=True, **kwargs)
            
            logger.info("Starting streaming completion", 
                       model=request_data["model"],
                       message_count=len(messages))
            
            # Make streaming API call
            async with self.client.stream("POST", "/chat/completions", json=request_data) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    
                    if line.startswith("data: "):
                        data = line[6:]  # Remove "data: " prefix
                        
                        if data.strip() == "[DONE]":
                            break
                        
                        try:
                            chunk_data = json.loads(data)
                            choices = chunk_data.get("choices", [])
                            
                            if choices:
                                delta = choices[0].get("delta", {})
                                content = delta.get("content", "")
                                
                                if content:
                                    yield content
                                    
                        except json.JSONDecodeError:
                            # Skip invalid JSON lines
                            continue
            
            logger.info("Streaming completion finished", 
                       model=request_data["model"])
                       
        except httpx.HTTPStatusError as e:
            context = {
                "model_name": model or self.config.llm_default,
                "status_code": e.response.status_code
            }
            raise create_llm_exception(e, context)
            
        except Exception as e:
            context = {"model_name": model or self.config.llm_default}
            raise create_llm_exception(e, context)
    
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """
        Holt verfügbare Models von OpenRouter
        
        Returns:
            Liste der verfügbaren Models
        """
        
        if not self._initialized:
            await self.initialize()
        
        try:
            response = await self.client.get("/models")
            response.raise_for_status()
            
            data = response.json()
            models = data.get("data", [])
            
            logger.info("Retrieved available models", count=len(models))
            return models
            
        except Exception as e:
            logger.error("Failed to get available models", error=str(e))
            raise create_llm_exception(e)


# Global LLM Service Instance (Singleton Pattern)
_llm_service: Optional[LLMService] = None


async def get_llm_service() -> LLMService:
    """
    Singleton Getter für LLM Service
    
    Returns:
        Initialized LLM Service instance
    """
    global _llm_service
    
    if _llm_service is None:
        _llm_service = LLMService()
        await _llm_service.initialize()
    
    return _llm_service


async def close_llm_service() -> None:
    """
    Schließt global LLM Service
    Wird beim App-Shutdown aufgerufen
    """
    global _llm_service
    
    if _llm_service is not None:
        await _llm_service.close()
        _llm_service = None 