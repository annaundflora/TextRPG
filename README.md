# TextRPG - Simplified MVP Architecture

Ein generatives TextRPG mit zwei spezialisierten AI-Agenten, drastisch vereinfacht für MVP.

## 🚀 Vereinfachte Architektur (Post-Refactoring)

### Agent System
- **Story Creator Agent**: Generiert fesselnde Kapitel (800-1200 Wörter)
- **Gamemaster Agent**: Verarbeitet Spieleraktionen und bietet Handlungsoptionen

### Einfache Agent-Wechsel
- **Story Creator → Gamemaster**: `--- HANDLUNGSOPTIONEN ---` Marker
- **Gamemaster → Story Creator**: `--- WEITER MIT GESCHICHTE ---` Marker
- Keine komplexen Pattern-Matching oder Regex-Erkennung

### Technologie-Stack

#### Backend
- **FastAPI**: REST API + Server-Sent Events (SSE) für Streaming
- **LangChain + LangGraph**: Vereinfachte Agent-Orchestrierung
- **OpenRouter**: LLM-Integration
- **Pydantic**: Minimales State Management

#### Frontend  
- **React + TypeScript**: Type-sichere UI-Komponenten
- **Vite**: Build-Tool und Dev-Server
- **TailwindCSS**: Utility-first Styling
- **SSE Integration**: Streaming Chat-Interface

## 📁 Vereinfachte Projektstruktur

```
TextRPG/
├── backend/app/
│   ├── agents/          # Agent-Implementierungen
│   ├── graph/           # Vereinfachte LangGraph Workflows
│   │   ├── workflow.py  # Einfacher Agent-Workflow (~100 Zeilen)
│   │   ├── nodes_agents.py # Generic Agent Node (~200 Zeilen)
│   │   └── session_manager.py
│   ├── models/          # Minimales State Model
│   │   └── state.py     # ChatState (~120 Zeilen, 7 Felder)
│   ├── routes/          # FastAPI Endpoints
│   └── services/        # LLM Services
├── backend/prompts/     # Agent-Prompts mit Marker-Instruktionen
├── frontend/src/        # React Frontend
└── project_notes/       # Architektur-Dokumentation
```

## 🔄 Vereinfachter Workflow

### 1. Einfacher State
```python
class ChatState(BaseModel):
    session_id: str
    messages: List[ChatMessage]
    current_agent: Optional[AgentType] = "story_creator"
    processing: bool = False
    last_user_message: Optional[str] = None
    active: bool = True
    created_at: datetime
    last_updated: datetime
```

### 2. Generic Agent Node
```python
async def generic_agent_node(state: ChatState, agent_type: AgentType):
    # Eine Funktion für beide Agents
    # Eliminiert Code-Duplikation
    # Parameter-basierte Agent-Unterscheidung
```

### 3. Marker-basierte Transitions
```python
# Einfache Marker-Erkennung
GAMEMASTER_MARKER = "--- HANDLUNGSOPTIONEN ---"
STORY_CREATOR_MARKER = "--- WEITER MIT GESCHICHTE ---"

def should_transition_to_gamemaster(state):
    return GAMEMASTER_MARKER in get_last_ai_message(state)
```

## 📊 Vereinfachungs-Erfolg

### Vorher vs. Nachher
| Komponente | Vorher | Nachher | Reduzierung |
|------------|--------|---------|-------------|
| **State Model** | 323 Zeilen, 20+ Felder | 122 Zeilen, 7 Felder | -62% |
| **Agent Nodes** | 457 Zeilen, dupliziert | 207 Zeilen, generisch | -55% |
| **Transitions** | 313 Zeilen, Regex/Pattern | 70 Zeilen, einfache Marker | -78% |
| **Workflow** | 259 Zeilen, 3-Phasen-System | 100 Zeilen, direktes Routing | -61% |
| **Gesamt** | ~1350 Zeilen | ~500 Zeilen | **-63%** |

### Entfernte Komplexität
- ❌ 3-Phasen-System (setup/story/gameplay)
- ❌ Action-Count-basierte Übergänge
- ❌ Pattern-Matching mit Regex
- ❌ Natural Breakpoints Erkennung
- ❌ Komplexe Transition-Trigger
- ❌ Setup-Completion-Logic
- ❌ Character-Info-Extraktion
- ❌ Übermäßiges Logging
- ❌ Duplicate Code zwischen Agents

### Beibehaltene Features
- ✅ Zwei spezialisierte Agents
- ✅ Automatische Agent-Wechsel
- ✅ Streaming Chat-Interface
- ✅ Session Management
- ✅ Error Handling (vereinfacht)
- ✅ Type Safety
- ✅ Flexible, nicht-lineare Spielabläufe

## 🎮 Spielablauf

### Vereinfachter Flow
1. **Start**: Immer mit Story Creator
2. **Story Phase**: Story Creator generiert Kapitel
3. **Action Phase**: Bei `--- HANDLUNGSOPTIONEN ---` → Gamemaster
4. **Interaction**: Gamemaster verarbeitet Aktionen
5. **Continue**: Bei `--- WEITER MIT GESCHICHTE ---` → Story Creator
6. **Repeat**: Flexibler Wechsel basierend auf Kontext

### Vorteile für MVP
- **Einfacher zu verstehen** und zu debuggen
- **Schnellere Entwicklung** neuer Features
- **Weniger Bugs** durch reduzierte Komplexität
- **Bessere Performance** durch weniger Overhead
- **Flexiblerer Spielablauf** ohne starre Regeln

## 🛠️ Development Setup

### Backend
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm run dev
```

### Environment Variables
```
OPENROUTER_API_KEY=your_key_here
LLM_CREATOR=google/gemini-2.0-flash-exp
LLM_GAMEMASTER=google/gemini-2.5-flash-preview
```

## 📝 Agent-Prompts

### Story Creator
- Generiert 800-1200 Wort Kapitel
- Fügt `--- HANDLUNGSOPTIONEN ---` hinzu wenn Spieleraktionen nötig
- Fokus auf atmosphärische Erzählung

### Gamemaster  
- Verarbeitet Spieleraktionen (100-300 Wörter)
- Bietet kreative Handlungsoptionen
- Fügt `--- WEITER MIT GESCHICHTE ---` hinzu für Story-Fortsetzung

## 🎯 Nächste Schritte

1. **Testing**: Verschiedene Spielszenarien testen
2. **UI Polish**: Frontend-Verbesserungen
3. **Performance**: Streaming-Optimierung
4. **Features**: Basierend auf User-Feedback

---

**Ergebnis**: Ein wartbares, verständliches MVP-System mit 63% weniger Code bei gleicher Funktionalität. 