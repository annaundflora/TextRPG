from typing import Optional, Tuple, Dict, Any
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage
from .base_agent import BaseAgent
from .prompt_loader import get_story_creator_prompt
import logging

logger = logging.getLogger(__name__)


class StoryCreatorAgent(BaseAgent):
    """Agent für die Erstellung von Story-Kapiteln."""
    
    def __init__(self, llm: BaseChatModel):
        super().__init__(llm, "Story Creator")
        self.load_prompt()
        
    def load_prompt(self) -> None:
        """Lädt den vollständigen Story Creator Prompt aus der Markdown-Datei."""
        try:
            self.system_prompt = get_story_creator_prompt()
            logger.info("Story Creator: Vollständiger Prompt erfolgreich geladen")
        except Exception as e:
            logger.error(f"Story Creator: Fehler beim Laden des Prompts: {e}")
            # Fallback zu Placeholder
            self.system_prompt = """Du bist der Story Creator für ein TextRPG.
            
DEINE AUFGABE:
- Erstelle fesselnde Story-Kapitel
- Beende jedes Kapitel mit "--- HANDLUNGSOPTIONEN ---"
- Nach diesem Marker liste 3-4 mögliche Handlungen auf

BEISPIEL-FORMAT:
[Story-Text hier...]

--- HANDLUNGSOPTIONEN ---
1. Option A
2. Option B
3. Option C

WICHTIG: Verwende IMMER genau den Marker "--- HANDLUNGSOPTIONEN ---" am Ende!"""
        
    def process_message(self, messages: list[BaseMessage], state: Dict[str, Any]) -> Tuple[str, bool, Optional[str]]:
        """Override to add debugging"""
        logger.info(f"Story Creator: Processing {len(messages)} messages")
        for i, msg in enumerate(messages):
            msg_type = type(msg).__name__
            content_preview = msg.content[:100] if hasattr(msg, 'content') else str(msg)[:100]
            logger.info(f"  Message[{i}]: {msg_type} - {content_preview}")
        
        logger.info(f"Story Creator: State keys: {list(state.keys())}")
        
        # Call parent process_message
        response_text, should_transition, transition_trigger = super().process_message(messages, state)
        
        logger.info(f"Story Creator: Generated response of length {len(response_text)}")
        logger.info(f"Story Creator: Response preview: {response_text[:200]}")
        
        return response_text, should_transition, transition_trigger
        
    def detect_transition(self, response: str) -> Tuple[bool, Optional[str]]:
        """
        Prüft ob zum Gamemaster gewechselt werden soll.
        Trigger: "--- HANDLUNGSOPTIONEN ---" im Output (aus dem vollständigen Prompt)
        
        WICHTIG: Die initiale Setup-Frage sollte NICHT als Transition gelten!
        Nur echte Story-Handlungsoptionen sollen zum Gamemaster führen.
        """
        
        # Check für initiale Setup-Frage (sollte NICHT transitionieren)
        initial_question_markers = [
            "Möchtest du:",
            "A) Mir eigene Vorgaben geben",
            "B) Mich komplett frei eine Geschichte entwickeln lassen",
            "Was bevorzugst du?"
        ]
        
        # Wenn es eine initiale Setup-Frage ist, KEINE Transition
        for initial_marker in initial_question_markers:
            if initial_marker in response:
                logger.info(f"Story Creator: Initiale Setup-Frage erkannt, keine Transition")
                return False, None
        
        # Suche nach echten Handlungsoptionen-Markern
        transition_markers = [
            "--- HANDLUNGSOPTIONEN ---",
            "HANDLUNGSOPTIONEN:",
            "Handlungsoptionen:"
        ]
        
        for marker in transition_markers:
            if marker in response:
                logger.info(f"Story Creator: Transition zu Gamemaster erkannt via '{marker}'")
                return True, "handlungsoptionen_präsentiert"
        
        # Keine Transition erkannt
        return False, None
        
 