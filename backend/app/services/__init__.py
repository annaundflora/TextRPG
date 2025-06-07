"""
TextRPG Services Package
LLM Integration und Service Layer
"""

from .llm_service import (
    LLMService,
    get_llm_service,
    close_llm_service
)

from .langchain_llm_service import (
    LangChainLLMService,
    get_langchain_llm_service,
    close_langchain_llm_service
)

from .exceptions import (
    LLMServiceException,
    LLMErrorType,
    APIKeyInvalidException,
    APIRateLimitedException,
    ModelNotFoundException,
    ModelOverloadedException,
    NetworkTimeoutException,
    RequestTooLargeException,
    ResponseInvalidException,
    create_llm_exception,
    classify_error
)

__all__ = [
    # HTTP-based LLM Service (legacy)
    "LLMService",
    "get_llm_service", 
    "close_llm_service",
    
    # LangChain-based LLM Service (für LangSmith Tracing)
    "LangChainLLMService",
    "get_langchain_llm_service",
    "close_langchain_llm_service",
    
    # Exceptions
    "LLMServiceException",
    "LLMErrorType",
    "APIKeyInvalidException",
    "APIRateLimitedException",
    "ModelNotFoundException",
    "ModelOverloadedException",
    "NetworkTimeoutException",
    "RequestTooLargeException",
    "ResponseInvalidException",
    "create_llm_exception",
    "classify_error"
] 