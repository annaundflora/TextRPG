"""
TextRPG Services Package
LLM Integration und Service Layer
"""

from .llm_service import (
    LLMService,
    get_llm_service,
    close_llm_service
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
    # LLM Service
    "LLMService",
    "get_llm_service", 
    "close_llm_service",
    
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