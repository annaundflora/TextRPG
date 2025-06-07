# TextRPG - Generatives Text-Rollenspiel

Ein generatives TextRPG mit spezialisierten AI-Agenten, das auf LangGraph und FastAPI basiert.

## Aktueller Entwicklungsstand: Phase 1 (Foundation Chatbot)

### Implementierte Features
- ✅ Grundlegende Projektstruktur
- ✅ FastAPI Backend mit SSE Streaming
- ✅ React + TypeScript Frontend
- ✅ TailwindCSS Styling Setup
- ✅ Development Environment Configuration

### Geplante Features (Phase 2)
- 🔄 LangGraph Workflow mit Agent-Switching
- 🔄 Story Creator Agent
- 🔄 Gamemaster Agent
- 🔄 Automatische Transition Detection

## Technologie-Stack

### Backend
- **FastAPI**: REST API + Server-Sent Events (SSE)
- **LangChain + LangGraph**: Agent-Orchestrierung (Phase 2)
- **OpenRouter**: LLM-Integration
- **Pydantic**: Datenvalidierung

### Frontend
- **React + TypeScript**: Type-sichere UI
- **Vite**: Build-Tool und Development Server
- **TailwindCSS**: Utility-first CSS Framework
- **SSE Integration**: Streaming Chat Interface

## Installation & Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- npm oder yarn

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
```

### Frontend Setup
```bash
cd frontend
npm install
```

### Environment Configuration
Erstelle eine `.env` Datei im Projekt-Root:
```
OPENROUTER_API_KEY=your_key_here
LLM_DEFAULT=google/gemini-2.0-flash-exp
LLM_CREATOR=google/gemini-2.0-flash-exp
LLM_GAMEMASTER=google/gemini-2.5-flash-preview-05-20
```

## Development

### Backend starten
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### Frontend starten
```bash
cd frontend
npm run dev
```

Die Anwendung ist dann verfügbar unter:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Projektstruktur

```
TextRPG/
├── backend/app/
│   ├── agents/          # Agent-Implementierungen (Phase 2)
│   ├── graph/           # LangGraph Workflows (Phase 2)
│   ├── models/          # Pydantic Models
│   ├── routes/          # FastAPI Endpoints
│   └── services/        # LLM & Session Services
├── frontend/src/
│   ├── components/      # React UI Components
│   ├── hooks/          # Custom Hooks
│   ├── services/       # API Services
│   └── types/          # TypeScript Definitions
└── project_notes/      # Dokumentation & Prompts
```

## Agent-System (Phase 2)

Das Spiel wird von zwei spezialisierten AI-Agenten gesteuert:

### Story Creator Agent
- Generiert fesselnde Kapitel (800-1200 Wörter)
- Fokus auf narrative Qualität und Immersion
- Übergibt an Gamemaster bei Handlungsoptionen

### Gamemaster Agent
- Verarbeitet Spieleraktionen
- Bietet konkrete Handlungsoptionen
- Verwaltet Spieler-Charakterdaten

## Development Guidelines

### Code Style
- **Python**: Type Hints, Pydantic Models, Async/Await
- **TypeScript**: Strict Mode, Interface Definitions
- **Naming**: snake_case (Python), camelCase (TypeScript)

### Sprache
- **User Interface**: Deutsch
- **Code Comments**: Deutsch oder Englisch
- **Commit Messages**: Englisch

## Contributing

1. Feature Branch erstellen
2. Changes implementieren
3. Type Safety überprüfen
4. Tests ausführen (wenn vorhanden)
5. Pull Request erstellen

## Lizenz

[Lizenz Information hier einfügen]

---

**Entwicklungsphase**: Foundation Chatbot (Phase 1)  
**Nächste Schritte**: Agent Implementation und LangGraph Integration 