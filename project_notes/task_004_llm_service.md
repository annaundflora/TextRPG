# Task 4: LLM Service Integration mit OpenRouter

## Übersicht
**Status**: 🔄 In Bearbeitung  
**Priorität**: Hoch  
**Abhängigkeiten**: Task 1-3 (Backend Setup, Config, Models)

## Ziel
Implementierung einer LLM Service Klasse für OpenRouter API Integration mit async chat completion, proper error handling und model configuration für Phase 1.

## Technische Anforderungen

### Core Funktionalität
- OpenRouter API Client mit httpx/aiohttp
- Async chat completion calls
- Streaming response support (vorbereitung für SSE)
- Model configuration management
- Rate limiting und retry logic

### API Integration
```python
# Ziel-Interface:
async def chat_completion(
    messages: List[ChatMessage],
    model: str = None,
    stream: bool = False,
    **kwargs
) -> Union[ChatMessage, AsyncGenerator[str, None]]
```

### Error Handling
- Network errors (timeouts, connection issues)
- API errors (rate limits, invalid keys, model errors)
- Validation errors (malformed requests)
- Graceful degradation und fallback strategies

### Configuration
- Model selection aus settings (LLM_DEFAULT, LLM_CREATOR, LLM_GAMEMASTER)
- Request parameters (temperature, max_tokens, etc.)
- Timeout und retry configuration
- API endpoint und authentication

## Implementation Details

### Service Klasse Struktur
```python
class LLMService:
    def __init__(self, config: Settings)
    async def chat_completion(...) -> ChatMessage
    async def stream_completion(...) -> AsyncGenerator[str, None]
    async def validate_api_key(self) -> bool
    def _build_request(self, messages, model, **kwargs) -> dict
    def _handle_response(self, response) -> ChatMessage
    async def _handle_errors(self, error) -> None
```

### OpenRouter API Specs
- Base URL: `https://openrouter.ai/api/v1/chat/completions`
- Authentication: Bearer token in headers
- Request format: OpenAI-compatible
- Response format: Standard completion response

### Models für Phase 1
- **Primary**: `google/gemini-2.0-flash-exp` (LLM_DEFAULT)
- **Fallback**: Konfigurierbar über settings
- **Future**: Separate models für Creator/Gamemaster (Phase 2)

## Dateien zu erstellen

### 1. `backend/app/services/llm_service.py`
- Haupt LLM Service Klasse
- OpenRouter API Integration
- Async completion methods
- Error handling und logging

### 2. `backend/app/services/__init__.py`
- Service exports
- Convenience imports

### 3. `backend/app/services/exceptions.py`
- Custom exceptions für LLM errors
- Error classification
- Recovery strategies

## Testing Strategy

### Unit Tests
- API key validation
- Request/response handling
- Error scenarios
- Model selection logic

### Integration Tests  
- Real OpenRouter API calls (mit test key)
- Streaming functionality
- Timeout und retry behavior

### Mock Tests
- Network failure simulation
- Rate limiting scenarios
- Invalid response handling

## Performance Considerations

### Optimization
- Connection pooling mit httpx
- Request/response caching (optional)
- Timeout configuration tuning
- Memory management für streaming

### Monitoring
- Response time tracking
- Error rate monitoring
- Token usage tracking
- API quota management

## Security Aspects

### API Key Management
- Sichere Storage in settings
- No logging of API keys
- Validation on service initialization

### Input Validation
- Message content sanitization
- Request size limits
- Model parameter validation

## Dependencies

### Neue Requirements
```
# Bereits in requirements.txt:
httpx==0.25.2
aiohttp==3.9.1

# Möglicherweise zusätzlich:
tenacity==8.2.3  # für retry logic
```

### Internal Dependencies
- `app.config.settings` für API configuration
- `app.models` für Message/State types
- `app.utils` für logging utilities

## Success Criteria

### Funktional
- ✅ Erfolgreiche OpenRouter API connection
- ✅ Async chat completion working
- ✅ Error handling implementation
- ✅ Model configuration flexibility

### Non-Funktional
- Response time < 5s für normale requests
- Proper error recovery und user feedback
- Clean interface für LangGraph integration
- Extensible für Phase 2 Agent-specific models

## Phase 2 Vorbereitung

### Agent-Specific Models
```python
# Bereits in settings vorbereitet:
llm_creator: str = "google/gemini-2.0-flash-exp"
llm_gamemaster: str = "google/gemini-2.5-flash-preview-05-20"
```

### Context Management
- Agent-specific prompting
- Context window management
- Model switching logic
- Response format handling

## Implementation Reihenfolge

1. **Basic Service Setup** - LLMService Klasse mit config
2. **OpenRouter Integration** - API client implementation
3. **Error Handling** - Comprehensive error management
4. **Testing** - Unit und integration tests
5. **Performance Tuning** - Optimization und monitoring
6. **Documentation** - API docs und examples

## Bekannte Herausforderungen

### API Limits
- OpenRouter rate limiting
- Model availability
- Cost management

### Streaming
- SSE preparation ohne immediate usage
- Memory management für lange responses
- Connection handling

### Error Recovery
- Network instability
- API outages
- Model overload scenarios 