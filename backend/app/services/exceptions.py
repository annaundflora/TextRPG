"""
TextRPG LLM Service Exceptions
Custom Exceptions für LLM-Integration und Error Handling
"""

from typing import Optional, Dict, Any
from enum import Enum


class LLMErrorType(Enum):
    """Classification von LLM-Fehlern für besseres Error Handling"""
    
    # API-bezogene Fehler
    API_KEY_INVALID = "api_key_invalid"
    API_RATE_LIMITED = "api_rate_limited"
    API_QUOTA_EXCEEDED = "api_quota_exceeded"
    API_UNAVAILABLE = "api_unavailable"
    
    # Network-bezogene Fehler
    NETWORK_TIMEOUT = "network_timeout"
    NETWORK_CONNECTION = "network_connection"
    NETWORK_DNS = "network_dns"
    
    # Model-bezogene Fehler
    MODEL_NOT_FOUND = "model_not_found"
    MODEL_OVERLOADED = "model_overloaded"
    MODEL_CONTEXT_LENGTH = "model_context_length"
    
    # Request-bezogene Fehler
    REQUEST_INVALID = "request_invalid"
    REQUEST_TOO_LARGE = "request_too_large"
    REQUEST_MALFORMED = "request_malformed"
    
    # Response-bezogene Fehler
    RESPONSE_INVALID = "response_invalid"
    RESPONSE_TRUNCATED = "response_truncated"
    RESPONSE_EMPTY = "response_empty"
    
    # Interne Fehler
    INTERNAL_ERROR = "internal_error"
    CONFIGURATION_ERROR = "configuration_error"
    UNKNOWN_ERROR = "unknown_error"


class LLMServiceException(Exception):
    """
    Basis Exception für alle LLM Service Fehler
    """
    
    def __init__(
        self,
        message: str,
        error_type: LLMErrorType,
        original_error: Optional[Exception] = None,
        error_details: Optional[Dict[str, Any]] = None,
        recoverable: bool = False,
        retry_after: Optional[int] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.original_error = original_error
        self.error_details = error_details or {}
        self.recoverable = recoverable
        self.retry_after = retry_after
    
    def __str__(self) -> str:
        return f"LLMServiceException[{self.error_type.value}]: {self.message}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert Exception zu dict für Logging/API Response"""
        return {
            "error_type": self.error_type.value,
            "message": self.message,
            "recoverable": self.recoverable,
            "retry_after": self.retry_after,
            "error_details": self.error_details,
            "original_error": str(self.original_error) if self.original_error else None
        }


class APIKeyInvalidException(LLMServiceException):
    """OpenRouter API Key ist ungültig oder fehlt"""
    
    def __init__(self, message: str = "OpenRouter API Key ist ungültig oder nicht gesetzt"):
        super().__init__(
            message=message,
            error_type=LLMErrorType.API_KEY_INVALID,
            recoverable=False
        )


class APIRateLimitedException(LLMServiceException):
    """API Rate Limit erreicht"""
    
    def __init__(self, retry_after: Optional[int] = None, message: str = "API Rate Limit erreicht"):
        super().__init__(
            message=message,
            error_type=LLMErrorType.API_RATE_LIMITED,
            recoverable=True,
            retry_after=retry_after
        )


class ModelNotFoundException(LLMServiceException):
    """Angefordertes Model nicht verfügbar"""
    
    def __init__(self, model_name: str):
        super().__init__(
            message=f"Model '{model_name}' nicht verfügbar oder nicht gefunden",
            error_type=LLMErrorType.MODEL_NOT_FOUND,
            recoverable=False,
            error_details={"model_name": model_name}
        )


class ModelOverloadedException(LLMServiceException):
    """Model ist überlastet"""
    
    def __init__(self, model_name: str, retry_after: Optional[int] = None):
        super().__init__(
            message=f"Model '{model_name}' ist derzeit überlastet",
            error_type=LLMErrorType.MODEL_OVERLOADED,
            recoverable=True,
            retry_after=retry_after,
            error_details={"model_name": model_name}
        )


class NetworkTimeoutException(LLMServiceException):
    """Network Timeout beim API Call"""
    
    def __init__(self, timeout_seconds: float):
        super().__init__(
            message=f"Network timeout nach {timeout_seconds}s",
            error_type=LLMErrorType.NETWORK_TIMEOUT,
            recoverable=True,
            error_details={"timeout_seconds": timeout_seconds}
        )


class RequestTooLargeException(LLMServiceException):
    """Request überschreitet Size Limits"""
    
    def __init__(self, size_bytes: int, max_size: int):
        super().__init__(
            message=f"Request zu groß: {size_bytes} bytes (max: {max_size})",
            error_type=LLMErrorType.REQUEST_TOO_LARGE,
            recoverable=False,
            error_details={"size_bytes": size_bytes, "max_size": max_size}
        )


class ResponseInvalidException(LLMServiceException):
    """API Response ist invalid oder unerwartetes Format"""
    
    def __init__(self, details: str = ""):
        super().__init__(
            message=f"Invalid API response{': ' + details if details else ''}",
            error_type=LLMErrorType.RESPONSE_INVALID,
            recoverable=True,
            error_details={"details": details}
        )


def classify_error(error: Exception) -> LLMErrorType:
    """
    Klassifiziert einen generischen Error in LLMErrorType
    
    Args:
        error: Original Exception
        
    Returns:
        Entsprechender LLMErrorType
    """
    
    error_str = str(error).lower()
    
    # HTTP Status Code basierte Classification
    if hasattr(error, 'status_code'):
        status = error.status_code
        if status == 401:
            return LLMErrorType.API_KEY_INVALID
        elif status == 429:
            return LLMErrorType.API_RATE_LIMITED
        elif status == 404:
            return LLMErrorType.MODEL_NOT_FOUND
        elif status == 503:
            return LLMErrorType.MODEL_OVERLOADED
        elif 400 <= status < 500:
            return LLMErrorType.REQUEST_INVALID
        elif 500 <= status < 600:
            return LLMErrorType.API_UNAVAILABLE
    
    # String-basierte Classification
    if any(keyword in error_str for keyword in ['timeout', 'timed out']):
        return LLMErrorType.NETWORK_TIMEOUT
    elif any(keyword in error_str for keyword in ['connection', 'connect']):
        return LLMErrorType.NETWORK_CONNECTION
    elif any(keyword in error_str for keyword in ['dns', 'resolve']):
        return LLMErrorType.NETWORK_DNS
    elif any(keyword in error_str for keyword in ['too large', 'payload']):
        return LLMErrorType.REQUEST_TOO_LARGE
    elif any(keyword in error_str for keyword in ['invalid', 'malformed']):
        return LLMErrorType.REQUEST_MALFORMED
    
    # Default fallback
    return LLMErrorType.UNKNOWN_ERROR


def create_llm_exception(
    error: Exception,
    context: Optional[Dict[str, Any]] = None
) -> LLMServiceException:
    """
    Factory Function für LLMServiceException basierend auf Original Error
    
    Args:
        error: Original Exception
        context: Additional context information
        
    Returns:
        Entsprechende LLMServiceException
    """
    
    error_type = classify_error(error)
    context = context or {}
    
    # Spezifische Exception Types
    if error_type == LLMErrorType.API_KEY_INVALID:
        return APIKeyInvalidException()
    elif error_type == LLMErrorType.API_RATE_LIMITED:
        retry_after = getattr(error, 'retry_after', None) or context.get('retry_after')
        return APIRateLimitedException(retry_after=retry_after)
    elif error_type == LLMErrorType.MODEL_NOT_FOUND:
        model_name = context.get('model_name', 'unknown')
        return ModelNotFoundException(model_name)
    elif error_type == LLMErrorType.MODEL_OVERLOADED:
        model_name = context.get('model_name', 'unknown')
        retry_after = getattr(error, 'retry_after', None) or context.get('retry_after')
        return ModelOverloadedException(model_name, retry_after)
    elif error_type == LLMErrorType.NETWORK_TIMEOUT:
        timeout = context.get('timeout_seconds', 0)
        return NetworkTimeoutException(timeout)
    elif error_type == LLMErrorType.REQUEST_TOO_LARGE:
        size_bytes = context.get('size_bytes', 0)
        max_size = context.get('max_size', 0)
        return RequestTooLargeException(size_bytes, max_size)
    elif error_type == LLMErrorType.RESPONSE_INVALID:
        details = context.get('details', str(error))
        return ResponseInvalidException(details)
    
    # Generic LLMServiceException als Fallback
    return LLMServiceException(
        message=str(error),
        error_type=error_type,
        original_error=error,
        error_details=context,
        recoverable=error_type in [
            LLMErrorType.API_RATE_LIMITED,
            LLMErrorType.MODEL_OVERLOADED,
            LLMErrorType.NETWORK_TIMEOUT,
            LLMErrorType.NETWORK_CONNECTION,
            LLMErrorType.API_UNAVAILABLE,
            LLMErrorType.RESPONSE_INVALID
        ]
    ) 