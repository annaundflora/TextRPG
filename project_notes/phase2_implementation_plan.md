# Phase 2 Implementation Plan: Story Creator & Gamemaster Agents

**Ziel:** Implementation der spezialisierten AI-Agents mit automatischem Agent-Switching für das TextRPG

**Datum:** Dezember 2024  
**Status:** In Progress

## Überblick

Phase 2 erweitert die Phase 1 Foundation um:
- Story Creator Agent für fesselnde Kapitel-Generierung
- Gamemaster Agent für Spieleraktions-Verarbeitung  
- Automatisches Agent-Switching basierend auf Transition-Triggern
- Enhanced State Management für Agent-Handoff

## Task Overview

| Task ID | Title | Status | Priority | Dependencies |
|---------|-------|--------|----------|-------------|
| task-25 | Agent-Klassen erstellen | ✅ **DONE** | High | - |
| task-26 | Prompts laden und integrieren | 🔄 **IN PROGRESS** | High | task-25 |
| task-27 | State für Agent-Management erweitern | ⏳ **PENDING** | High | task-25 |
| task-28 | Graph Nodes für beide Agents | ⏳ **PENDING** | High | task-26, task-27 |
| task-29 | Workflow mit Agent-Routing | ⏳ **PENDING** | High | task-28 |
| task-30 | Frontend Agent-Anzeige | ⏳ **PENDING** | Medium | task-29 |
| task-31 | End-to-End Testing | ⏳ **PENDING** | High | task-30 |

## Detaillierte Task-Beschreibungen

### ✅ Task 1: Agent-Klassen erstellen
**Status:** Abgeschlossen und getestet

**Implementierung:**
- `BaseAgent` abstrakte Klasse mit gemeinsamer Logik
- `StoryCreatorAgent` mit Placeholder-Prompt und Transition-Detection
- `GamemasterAgent` mit Placeholder-Prompt und Transition-Detection
- Test-Skript für isolierte Agent-Tests

**Deliverables:**
- ✅ `backend/app/agents/base_agent.py`
- ✅ `backend/app/agents/story_creator.py` 
- ✅ `backend/app/agents/gamemaster.py`
- ✅ `backend/app/agents/__init__.py`
- ✅ `backend/app/test_agents.py`

**Test-Ergebnisse:**
- ✅ Story Creator generiert "--- HANDLUNGSOPTIONEN ---" Trigger
- ✅ Gamemaster generiert "--- STORY CREATOR ÜBERGANG ---" Trigger
- ✅ Beide Agents kommunizieren erfolgreich mit OpenRouter API
- ✅ Transition Detection funktioniert korrekt

---

### 🔄 Task 2: Prompts laden und integrieren
**Status:** Bereit zum Start

**Ziel:** Vollständige Prompts aus `project_notes/prompt_*.md` in die Agents laden

**Arbeitsschritte:**
1. Prompt-Loader Funktion erstellen mit UTF-8 Support
2. `story_creator.py` um vollständigen Prompt erweitern
3. `gamemaster.py` um vollständigen Prompt erweitern
4. Test-Integration und Validation

**Erwartete Dateien:**
- `project_notes/prompt_story_creator.md`
- `project_notes/prompt_game_master.md`

---

### ⏳ Task 3: State für Agent-Management erweitern
**Status:** Pending (abhängig von Task 2)

**Ziel:** ChatState erweitern für Agent-Handoff und Context-Preservation

**Neue State-Felder:**
- `current_agent`: Aktueller Agent (story_creator/gamemaster)
- `transition_trigger`: Grund für letzten Agent-Switch
- `story_context`: Story-Kontext für Kontinuität
- `character_info`: Spieler-Charakterdaten
- `agent_handoff_context`: Explizite Übergabe-Informationen

**Dateien zu modifizieren:**
- `backend/app/models/state.py`

---

### ⏳ Task 4: Graph Nodes für beide Agents
**Status:** Pending (abhängig von Task 2, 3)

**Ziel:** LangGraph Node-Functions implementieren

**Arbeitsschritte:**
1. `story_creator_node()` in `graph/nodes.py`
2. `gamemaster_node()` in `graph/nodes.py`
3. Transition-Logic in beide Nodes einbauen
4. Error Handling und Logging

---

### ⏳ Task 5: Workflow mit Agent-Routing
**Status:** Pending (abhängig von Task 4)

**Ziel:** LangGraph Workflow erweitern um Conditional Edges

**Routing-Logic:**
- Entry Point: Immer `story_creator` für neue Sessions
- story_creator → gamemaster: Bei "handlungsoptionen_präsentiert"
- gamemaster → story_creator: Bei "neues_kapitel_benötigt"
- END-State: Bei Session-Reset oder Errors

**Dateien zu modifizieren:**
- `backend/app/graph/workflow.py`

---

### ⏳ Task 6: Frontend Agent-Anzeige
**Status:** Pending (abhängig von Task 5)

**Ziel:** Chat-Interface erweitern um Agent-Visualisierung

**Features:**
- Aktueller Agent anzeigen (Story Creator / Gamemaster)
- Optional: Unterschiedliche Styling für verschiedene Agents
- Agent-Transition Feedback

**Dateien zu modifizieren:**
- Frontend Chat-Komponenten
- State Management für Agent-Anzeige

---

### ⏳ Task 7: End-to-End Testing
**Status:** Pending (abhängig von Task 6)

**Ziel:** Kompletten Agent-Switching Flow testen

**Test-Szenario:**
1. **Start:** Story Creator generiert erstes Kapitel
2. **Trigger:** "--- HANDLUNGSOPTIONEN ---" → Switch zu Gamemaster
3. **Aktion:** Spieler wählt Handlungsoption
4. **Verarbeitung:** Gamemaster verarbeitet Aktion
5. **Trigger:** "--- STORY CREATOR ÜBERGANG ---" → Switch zu Story Creator
6. **Fortsetzung:** Neues Kapitel wird generiert

## Technical Notes

### Transition Patterns
```
Story Creator → Gamemaster: "--- HANDLUNGSOPTIONEN ---"
Gamemaster → Story Creator: "--- STORY CREATOR ÜBERGANG ---"
```

### State Context Handoff
```python
# Story Creator → Gamemaster
story_context: Letzter Story-Kontext
character_info: Spieler-Charakterdaten

# Gamemaster → Story Creator  
agent_handoff_context: Aktions-Konsequenzen
story_context: Aktualisierter Kontext
```

### Testing Strategy
- **Unit Tests:** Einzelne Agent-Logik
- **Integration Tests:** Agent-Switching im LangGraph
- **E2E Tests:** Kompletter User-Flow
- **Manual Tests:** UI und UX Validation

## Success Criteria

Phase 2 ist erfolgreich wenn:
- [x] Agent-Klassen funktionieren isoliert
- [ ] Vollständige Prompts sind integriert
- [ ] Agent-Switching funktioniert automatisch
- [ ] State wird korrekt zwischen Agents übertragen
- [ ] Frontend zeigt aktuellen Agent an
- [ ] Kompletter Story-Flow funktioniert End-to-End

## Next Steps

1. **Sofort:** Task 2 starten (Prompts laden)
2. **Nach Task 2:** Task 3 parallel zu Task 2 möglich
3. **Iterativ:** Nach jedem Task testen
4. **Final:** Komplettes E2E Testing

---

*Letzte Aktualisierung: Nach erfolgreichem Abschluss von Task 1* 