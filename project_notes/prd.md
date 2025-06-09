# TextRPG MVP - Product Requirements Document

## Produktvision

**Ein TextRPG-System mit generativen Kapiteln und hohem Wiederspielwert, basierend auf einem 2-Agent System mit Silent Handoffs für nahtlose User Experience.**

## MVP Scope

**Core Value**: User erlebt fließende Story-to-Interaction Übergänge ohne sichtbare System-Transitionen oder fragmentierte Ausgaben.

**Out of Scope**: Character Creator, Character Manager, komplexe Branching Stories, Advanced Error Recovery

## Funktionale Anforderungen

### F0: Story-Längen Definition
- **Initial-Kapitel**: 600-800 Wörter (ausführliche Einführung)
- **Folge-Kapitel**: 200-400 Wörter (mobile-optimiert)
- **Action-Responses**: 100-200 Wörter (schnell und reaktiv)

### F1: Setup Agent
**Zweck**: Sammelt initiale Spieler-Präferenzen für Story-Generierung

#### F1.1 Setup-Informationen sammeln
- **MUSS** Setting/Genre vom Spieler erfragen (bei guided mode)
- **MUSS** Schwierigkeitsgrad erfragen (bei guided mode)
- **MUSS** bei free mode nur nach Ausschluss-Kriterien fragen
- **MUSS** Setup-Vollständigkeit validieren
- **MUSS** bei unvollständigem Setup weitere Fragen stellen

#### F1.2 Setup-Completion Detection
- **MUSS** erkennen wann genügend Informationen gesammelt wurden
- **MUSS** deterministisch zu Gameplay Agent überleiten
- **DARF** keine User-Response nach Setup-Completion ausgeben

#### F1.3 Setup-Context Übergabe
- **MUSS** Setup-Daten strukturiert an Gameplay Agent übergeben
- **MUSS** handoff_data für Silent Transfer nutzen
- **MUSS** Setup-Phase als "abgeschlossen" markieren

### F2: Gameplay Agent
**Zweck**: Generiert Stories und verwaltet Player-Interaktionen

#### F2.1 Story Generation mit Silent Handoff
- **MUSS** handoff_data vom Setup Agent empfangen
- **MUSS** Initial-Kapitel (600-800 Wörter) generieren
- **MUSS** Folge-Kapitel (200-400 Wörter) generieren
- **MUSS** kontextuelle Handlungsoptionen erstellen
- **MUSS** Story + Options in einer einheitlichen Response kombinieren
- **DARF** keine separaten Story-Nachrichten vor Options ausgeben

#### F2.2 Player Action Processing
- **MUSS** Player-Aktionen auf verfügbare Optionen validieren
- **MUSS** Aktions-Konsequenzen (100-200 Wörter) verarbeiten
- **MUSS** neuen Scene-State basierend auf Aktionen erstellen
- **MUSS** neue Handlungsoptionen für aktualisierte Szene generieren

#### F2.3 Story Progression Management
- **MUSS** erkennen wann neue Story-Kapitel erforderlich sind
- **MUSS** Scene-Kontinuität zwischen Kapiteln wahren
- **MUSS** Session-Ende bei Story-Abschluss verwalten
- **MUSS** Session-Limits überwachen (max_chapters: 5, max_interactions: 20)
- **MUSS** End-Trigger erkennen (quest_complete, player_death, explicit_end)

#### F2.4 Command-based Story Flow
- **MUSS** Command für Gameplay→Gameplay Transitionen (neue Kapitel)
- **MUSS** Command für Gameplay→End Transition (Session beenden)
- **SOLLTE** State konsistent zwischen Transitionen halten

### F3: Agent Communication
**Zweck**: Zuverlässige Agent-zu-Agent Kommunikation

#### F3.1 Command-based Transitions
- **MUSS** LangGraph Command-Pattern für Agent-Übergaben nutzen
- **MUSS** State-Updates mit Transition-Kommandos kombinieren
- **DARF NICHT** Marker-basierte String-Parsing für Transitions verwenden

#### F3.2 Silent Handoff Mechanik
- **MUSS** Setup Agent → Gameplay Agent ohne User-sichtbare Transition
- **MUSS** handoff_data zwischen Agents übertragen
- **MUSS** handoff_data nach Verarbeitung cleanup

## Technische Anforderungen

### T1: State Management
```python
State Schema:
{
    "messages": list[BaseMessage],      # User-facing messages
    "setup_context": dict,              # Collected setup data
    "scene_context": dict,              # Current scene state  
    "story_phase": "setup"|"gameplay"|"end",  # Flow control
    "handoff_data": Optional[dict],     # Agent-to-agent data transfer
    "chapter_count": int,               # Track story progression
    "interaction_count": int,           # Track total interactions
}
```

### T2: LangGraph Implementation
- **MUSS** LangGraph StateGraph mit Command-Returns nutzen
- **MUSS** TypedDict für State Schema verwenden
- **MUSS** Agent-Nodes als Python-Funktionen implementieren
- **MUSS** deterministische Setup → Gameplay Transition

### T3: Message Role Management
- **MUSS** korrekte Message-Rollen verwenden (human/assistant)
- **MUSS** Agent-Attribution in AI-Messages
- **DARF NICHT** alle Messages als "system" Role verwenden
- **MUSS** Messages wie folgt strukturieren:
  - User-Input: role="human"
  - Agent-Response: role="assistant" 
  - Metadata in message.metadata speichern (agent_name, timestamp)

### T4: Error Handling (minimal)
- **MUSS** Iteration-Counter gegen infinite loops
- **MUSS** Basic Exception-Handling in Agent-Nodes
- **SOLLTE** Graceful degradation bei Agent-Failures

## User Stories

### US1: Setup Flow
**Als** neuer Spieler  
**Möchte ich** durch Setup-Fragen geführt werden  
**Damit** meine Präferenzen für die Story berücksichtigt werden

**Acceptance Criteria:**
- Setup Agent stellt klare, verständliche Fragen
- Bei "free mode" nur Ausschluss-Kriterien erfragen
- Spieler kann Setup in 2-4 Interaktionen abschließen
- Übergang zu Story ist nahtlos (keine sichtbare System-Transition)

### US2: Story + Interaction
**Als** Spieler  
**Möchte ich** Story und Handlungsoptionen in einer Antwort erhalten  
**Damit** das Spiel flüssig und immersiv ist

**Acceptance Criteria:**
- Eine einheitliche Response mit Story + Options
- Initial-Kapitel sind ausführlich (600-800 Wörter)
- Folge-Kapitel sind fokussiert (200-400 Wörter)
- Handlungsoptionen sind kontextuell relevant
- Keine fragmentierten oder doppelten Story-Ausgaben

### US3: Action Processing
**Als** Spieler  
**Möchte ich** Handlungen wählen und deren Konsequenzen erleben  
**Damit** ich aktiv die Story beeinflussen kann

**Acceptance Criteria:**
- Player-Aktionen werden sinnvoll verarbeitet
- Konsequenzen sind kurz und klar (100-200 Wörter)
- Neue Options reflektieren veränderte Situation

### US4: Story Progression
**Als** Spieler  
**Möchte ich** neue Story-Kapitel erleben wenn die aktuelle Szene abgeschlossen ist  
**Damit** die Geschichte fortschreitet

**Acceptance Criteria:**
- Automatische Story-Progression bei Major-Events
- Kontinuität zwischen Kapiteln
- Session-Limits werden respektiert (5 Kapitel, 20 Interaktionen)
- Klares Session-Ende bei Story-Abschluss

## Success Metrics

### Functional Success
- ✅ Setup Agent sammelt erfolgreich Setup-Daten (100% success rate)
- ✅ Silent Handoff Setup → Gameplay funktioniert (95%+ success rate)
- ✅ Story + Options werden unified ausgegeben (100% der time)
- ✅ Player Actions werden korrekt verarbeitet (95%+ success rate)
- ✅ Command-based Transitions funktionieren (100% success rate)

### User Experience Success
- ✅ Setup in ≤4 User-Interaktionen abgeschlossen
- ✅ Keine fragmentierten Story-Ausgaben für User sichtbar
- ✅ Story-to-Interaction Flow fühlt sich nahtlos an
- ✅ Session-Ende ist klar kommuniziert

### Technical Success
- ✅ Agent-Transitions funktionieren ohne Manual Intervention
- ✅ State wird korrekt zwischen Agents übertragen
- ✅ Message Roles sind korrekt gesetzt
- ✅ No infinite loops zwischen Agents

## Definition of Done

### MVP ist complete wenn:
1. **Setup Agent** sammelt User-Präferenzen und übergibt deterministisch
2. **Gameplay Agent** empfängt Setup, generiert unified Story+Options Response
3. **Story-Längen** sind differenziert (Initial: 600-800, Folge: 200-400, Actions: 100-200)
4. **Player Actions** werden verarbeitet mit sinnvollen Konsequenzen
5. **Story Progression** funktioniert für neue Kapitel
6. **Silent Handoffs** eliminieren fragmentierte User Experience
7. **Session Management** respektiert Limits und End-Trigger
8. **End-to-End Testing** bestätigt User Journey funktioniert

## Dependencies & Assumptions

### External Dependencies
- LangGraph Framework 
- LLM API (für Story- und Options-Generation)
- Story Generation Logic (aus Writing Glossary)

### Assumptions
- User akzeptiert 2-4 Setup-Fragen vor Story-Start
- Story-Generierung produziert kohärente Outputs
- LLM kann kontextuelle Handlungsoptionen generieren
- Basic A/B/C Options-Format ist für User ausreichend

### Technical Constraints
- Einzelne Session (keine Cross-Session Persistence)
- Text-only Interface (keine Audio/Visual Assets)
- Linear Story Progression (keine komplexe Branching-Logik)
- Keine Real-time Multiplayer Features