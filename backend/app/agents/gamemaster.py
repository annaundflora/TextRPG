from typing import Optional, Tuple
from langchain_core.language_models import BaseChatModel
from .base_agent import BaseAgent
from .prompt_loader import get_gamemaster_prompt
import logging

logger = logging.getLogger(__name__)


class GamemasterAgent(BaseAgent):
    """Agent für die Verarbeitung von Spieleraktionen."""
    
    def __init__(self, llm: BaseChatModel):
        super().__init__(llm, "Gamemaster")
        self.load_prompt()
        
    def load_prompt(self) -> None:
        """Lädt den vollständigen Gamemaster Prompt aus der Markdown-Datei."""
        try:
            self.system_prompt = get_gamemaster_prompt()
            logger.info("Gamemaster: Vollständiger Prompt erfolgreich geladen")
        except Exception as e:
            logger.error(f"Gamemaster: Fehler beim Laden des Prompts: {e}")
            # Fallback zu Placeholder
            self.system_prompt = """Du bist der Gamemaster für ein TextRPG.
            
DEINE AUFGABE:
- Verarbeite Spieleraktionen basierend auf den präsentierten Handlungsoptionen
- Beschreibe die direkten Konsequenzen der Aktion
- Beende mit "--- STORY CREATOR ÜBERGANG ---" wenn ein neues Kapitel beginnen soll

BEISPIEL-FORMAT:
[Verarbeitung der Spieleraktion...]
[Beschreibung der Konsequenzen...]

--- STORY CREATOR ÜBERGANG ---
Kontext für neues Kapitel: [Kurze Zusammenfassung]

WICHTIG: Verwende "--- STORY CREATOR ÜBERGANG ---" wenn die Story weitergehen soll!"""
        
    def detect_transition(self, response: str) -> Tuple[bool, Optional[str]]:
        """
        Prüft ob zurück zum Story Creator gewechselt werden soll.
        Trigger: "--- STORY CREATOR ÜBERGANG ---" im Output
        """
        if "--- STORY CREATOR ÜBERGANG ---" in response:
            logger.info("Gamemaster: Transition zu Story Creator erkannt")
            return True, "neues_kapitel_benötigt"
        
        return False, None 