# TextRPG MVP - Implementierungsleitfaden

## **Übersicht**
Dieser Leitfaden führt durch die konkrete Implementierung des TextRPG MVP basierend auf der [`mvp_architecture.md`](mvp_architecture.md).

## **Vorbereitung**

### **Repository Setup**
```bash
# Basis-Struktur erstellen
mkdir TextRPG
cd TextRPG
mkdir backend frontend project_notes
```

### **Environment Variables**
```bash
# .env erstellen
OPENROUTER_API_KEY=your_key_here
LLM_DEFAULT=google/gemini-2.0-flash-exp
LLM_CREATOR=google/gemini-2.0-flash-exp
LLM_GAMEMASTER=google/gemini-2.5-flash-preview-05-20
```

---

## **Phase 1: Foundation Chatbot**

### **Backend Implementation**

#### **1. FastAPI Setup**
```bash
cd backend
pip install fastapi uvicorn langchain langchain-openai langgraph pydantic pydantic-settings python-dotenv
```

**File: `app/main.py`**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.chat import router as chat_router
from routes.health import router as health_router

app = FastAPI(title="TextRPG API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(chat_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

#### **2. Configuration Management**
**File: `app/config.py`**
```python
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openrouter_api_key: str
    llm_default: str = "google/gemini-2.0-flash-exp"
    llm_creator: str = "google/gemini-2.0-flash-exp"
    llm_gamemaster: str = "google/gemini-2.5-flash-preview-05-20"
    
    class Config:
        env_file = ".env"

settings = Settings()
```

#### **3. State Models**
**File: `app/models/state.py`**
```python
from typing import List, Optional, Dict, Literal
from pydantic import BaseModel
from langchain_core.messages import BaseMessage

class ChatState(BaseModel):
    session_id: str
    messages: List[BaseMessage]
    
    # Phase 2 Extensions
    current_agent: Optional[Literal["story_creator", "gamemaster"]] = None
    story_context: Optional[str] = None
    character_info: Optional[Dict] = None
    world_state: Optional[Dict] = None
    transition_trigger: Optional[str] = None
    agent_handoff_context: Optional[str] = None
    
    created_at: Optional[str] = None
    last_updated: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True
```

#### **4. LLM Service**
**File: `app/services/llm_service.py`**
```python
from langchain_openai import ChatOpenAI
from app.config import settings

class LLMService:
    def __init__(self):
        self.base_config = {
            "base_url": "https://openrouter.ai/api/v1",
            "api_key": settings.openrouter_api_key,
            "streaming": True,
            "temperature": 0.7
        }
    
    def get_default_llm(self):
        return ChatOpenAI(model=settings.llm_default, **self.base_config)
    
    def get_creator_llm(self):
        return ChatOpenAI(model=settings.llm_creator, **self.base_config)
    
    def get_gamemaster_llm(self):
        return ChatOpenAI(model=settings.llm_gamemaster, **self.base_config)

llm_service = LLMService()
```

#### **5. Basic LangGraph Workflow**
**File: `app/graph/workflow.py`**
```python
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage
from app.models.state import ChatState
from app.graph.nodes import basic_chat_node
import uuid
from datetime import datetime

def create_basic_workflow():
    """Phase 1: Simple chat workflow"""
    workflow = StateGraph(ChatState)
    
    workflow.add_node("chat", basic_chat_node)
    workflow.set_entry_point("chat")
    workflow.add_edge("chat", END)
    
    return workflow.compile()

def create_session_state(user_message: str) -> ChatState:
    """Initialize new chat session"""
    return ChatState(
        session_id=str(uuid.uuid4()),
        messages=[HumanMessage(content=user_message)],
        created_at=datetime.now().isoformat(),
        last_updated=datetime.now().isoformat()
    )
```

**File: `app/graph/nodes.py`**
```python
from langchain_core.messages import AIMessage
from app.services.llm_service import llm_service
from app.models.state import ChatState
from datetime import datetime

def basic_chat_node(state: ChatState) -> ChatState:
    """Phase 1: Generic chat node"""
    llm = llm_service.get_default_llm()
    
    # Get LLM response
    response = llm.invoke(state.messages)
    
    # Update state
    state.messages.append(response)
    state.last_updated = datetime.now().isoformat()
    
    return state
```

#### **6. Chat Endpoints with Streaming**
**File: `app/routes/chat.py`**
```python
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from langchain_core.messages import HumanMessage
from app.graph.workflow import create_basic_workflow, create_session_state
import json
import asyncio

router = APIRouter(prefix="/api/chat")

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

@router.post("/stream")
async def chat_stream(request: ChatRequest):
    try:
        workflow = create_basic_workflow()
        
        # Create new session for Phase 1
        state = create_session_state(request.message)
        
        async def generate():
            try:
                # Stream workflow execution
                async for chunk in workflow.astream(state):
                    if "chat" in chunk:
                        last_message = chunk["chat"].messages[-1]
                        if hasattr(last_message, 'content'):
                            yield f"data: {json.dumps({'content': last_message.content, 'session_id': state.session_id})}\n\n"
                
                yield "data: [DONE]\n\n"
                
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/plain",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reset")
async def reset_session():
    """Reset current session"""
    return {"status": "session_reset"}
```

**File: `app/routes/health.py`**
```python
from fastapi import APIRouter

router = APIRouter()

@router.get("/api/health")
async def health_check():
    return {"status": "healthy"}
```

#### **7. Package Structure**
```bash
# Create __init__.py files
touch app/__init__.py
touch app/models/__init__.py
touch app/services/__init__.py
touch app/graph/__init__.py
touch app/routes/__init__.py
```

#### **8. Backend Test**
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
# Test: http://localhost:8000/api/health
```

### **Frontend Implementation**

#### **1. React Setup with Vite**
```bash
cd frontend
npm create vite@latest . -- --template react-ts
npm install uuid @types/uuid
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

#### **2. TypeScript Types**
**File: `src/types/chat.ts`**
```typescript
export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export interface ChatState {
  messages: Message[];
  isLoading: boolean;
  sessionId?: string;
  error?: string;
}

export interface StreamResponse {
  content?: string;
  session_id?: string;
  error?: string;
}
```

#### **3. Streaming Service**
**File: `src/services/streaming.ts`**
```typescript
import { StreamResponse } from '../types/chat';

export async function* streamChat(message: string, sessionId?: string): AsyncGenerator<StreamResponse> {
  const response = await fetch('/api/chat/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ message, session_id: sessionId }),
  });

  if (!response.body) {
    throw new Error('No response body');
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n');

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6);
          if (data === '[DONE]') return;
          
          try {
            const parsed: StreamResponse = JSON.parse(data);
            yield parsed;
          } catch (e) {
            yield { content: data };
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}
```

#### **4. Chat Hook**
**File: `src/hooks/useChat.ts`**
```typescript
import { useState, useCallback } from 'react';
import { Message, ChatState } from '../types/chat';
import { streamChat } from '../services/streaming';
import { v4 as uuidv4 } from 'uuid';

export function useChat() {
  const [state, setState] = useState<ChatState>({
    messages: [],
    isLoading: false,
  });

  const sendMessage = useCallback(async (content: string) => {
    const userMessage: Message = {
      id: uuidv4(),
      role: 'user',
      content,
      timestamp: new Date(),
    };

    setState(prev => ({
      ...prev,
      messages: [...prev.messages, userMessage],
      isLoading: true,
      error: undefined,
    }));

    try {
      let assistantContent = '';
      const assistantMessage: Message = {
        id: uuidv4(),
        role: 'assistant',
        content: '',
        timestamp: new Date(),
      };

      setState(prev => ({
        ...prev,
        messages: [...prev.messages, assistantMessage],
      }));

      for await (const chunk of streamChat(content, state.sessionId)) {
        if (chunk.error) {
          setState(prev => ({
            ...prev,
            error: chunk.error,
            isLoading: false,
          }));
          return;
        }

        if (chunk.content) {
          assistantContent += chunk.content;
          setState(prev => ({
            ...prev,
            messages: prev.messages.map(msg =>
              msg.id === assistantMessage.id
                ? { ...msg, content: assistantContent }
                : msg
            ),
          }));
        }

        if (chunk.session_id) {
          setState(prev => ({
            ...prev,
            sessionId: chunk.session_id,
          }));
        }
      }
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Unknown error',
      }));
    } finally {
      setState(prev => ({
        ...prev,
        isLoading: false,
      }));
    }
  }, [state.sessionId]);

  const resetChat = useCallback(async () => {
    try {
      await fetch('/api/chat/reset', { method: 'POST' });
      setState({
        messages: [],
        isLoading: false,
      });
    } catch (error) {
      console.error('Failed to reset chat:', error);
    }
  }, []);

  return {
    messages: state.messages,
    isLoading: state.isLoading,
    error: state.error,
    sendMessage,
    resetChat,
  };
}
```

#### **5. Chat Components**
**File: `src/components/ChatInterface.tsx`**
```typescript
import React from 'react';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';
import { useChat } from '../hooks/useChat';

export function ChatInterface() {
  const { messages, isLoading, error, sendMessage, resetChat } = useChat();

  return (
    <div className="flex flex-col h-screen max-w-4xl mx-auto p-4">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold">TextRPG Adventure</h1>
        <button
          onClick={resetChat}
          className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
        >
          New Adventure
        </button>
      </div>
      
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          Error: {error}
        </div>
      )}
      
      <MessageList messages={messages} isLoading={isLoading} />
      <MessageInput onSendMessage={sendMessage} disabled={isLoading} />
    </div>
  );
}
```

#### **6. Frontend Test**
```bash
cd frontend
npm run dev
# Test: http://localhost:5173
```

---

## **Phase 2: Agents & MVP Graph**

### **Agent Implementation**

#### **1. Story Creator Agent**
**File: `app/agents/story_creator.py`**
```python
from langchain_core.prompts import ChatPromptTemplate
from app.services.llm_service import llm_service
import os

class StoryCreatorAgent:
    def __init__(self):
        self.llm = llm_service.get_creator_llm()
        # Load prompt from project_notes
        prompt_path = os.path.join(os.path.dirname(__file__), "../../project_notes/prompt_story_creator.md")
        with open(prompt_path, "r", encoding="utf-8") as f:
            self.system_prompt = f.read()
    
    def generate_chapter(self, messages, context: dict) -> tuple[str, bool]:
        """Generate story chapter and determine if transition needed"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("human", "{user_input}")
        ])
        
        chain = prompt | self.llm
        response = chain.invoke({
            "user_input": messages[-1].content,
        })
        
        # Check for transition triggers
        should_transition = self._should_transition_to_gamemaster(response.content)
        
        return response.content, should_transition
    
    def _should_transition_to_gamemaster(self, response: str) -> bool:
        """Detect if story should transition to gamemaster"""
        transition_indicators = [
            "--- HANDLUNGSOPTIONEN ---",
            "What do you do?",
            "How do you respond?",
        ]
        return any(indicator in response for indicator in transition_indicators)
```

#### **2. Enhanced Workflow**
**File: `app/graph/workflow.py` (Enhanced)**
```python
# Add to existing workflow.py
from app.graph.nodes import story_creator_node, gamemaster_node

def create_game_workflow():
    """Phase 2: Full TextRPG workflow with agent switching"""
    workflow = StateGraph(ChatState)
    
    workflow.add_node("story_creator", story_creator_node)
    workflow.add_node("gamemaster", gamemaster_node)
    
    workflow.set_entry_point("story_creator")
    
    def agent_router(state: ChatState) -> str:
        if state.transition_trigger:
            if state.transition_trigger == "to_gamemaster":
                return "gamemaster"
            elif state.transition_trigger == "to_story_creator":
                return "story_creator"
        
        return state.current_agent or "story_creator"
    
    workflow.add_conditional_edges(
        "story_creator",
        agent_router,
        {
            "story_creator": "story_creator",
            "gamemaster": "gamemaster"
        }
    )
    
    workflow.add_conditional_edges(
        "gamemaster",
        agent_router,
        {
            "story_creator": "story_creator", 
            "gamemaster": "gamemaster"
        }
    )
    
    return workflow.compile()
```

---

## **Testing & Validation**

### **Phase 1 Testing**
1. **Backend Health Check**: `GET /api/health`
2. **Basic Chat**: Send message via `/api/chat/stream`
3. **Streaming**: Verify SSE response format
4. **Frontend**: Chat interface loads and sends messages

### **Phase 2 Testing**
1. **Agent Switching**: Verify automatic transitions
2. **Context Preservation**: Test story continuity
3. **Error Handling**: Invalid inputs, API failures
4. **Performance**: Response times, memory usage

---

## **Deployment**

### **Local Development**
```bash
# Terminal 1: Backend
cd backend && python -m uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend && npm run dev
```

### **Production Preparation**
- Docker containers für Backend
- Build und Deploy Pipeline
- Environment-spezifische Configs
- Monitoring und Logging

---

## **Troubleshooting**

### **Common Issues**
1. **CORS Errors**: Check FastAPI CORS configuration
2. **Streaming Issues**: Verify SSE headers and format
3. **Agent Not Switching**: Check transition trigger logic
4. **OpenRouter Errors**: Validate API key and model names

### **Debug Tools**
- FastAPI automatic docs: `http://localhost:8000/docs`
- Network tab für SSE debugging
- LangGraph visualization tools
- Console logging für state transitions

---

**Next Steps**: Nach Implementierung Phase 1 → Testing → Phase 2 → Finaler MVP Test 