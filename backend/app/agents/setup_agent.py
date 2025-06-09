"""
Setup Agent für TextRPG MVP - VEREINFACHTE VERSION
Keine Pattern Matching - das LLM übernimmt die gesamte Setup-Logik
"""

from typing import Dict, Any, Optional, Tuple, List, Literal
from langchain_core.messages import BaseMessage, AIMessage
from langchain_core.language_models import BaseChatModel
from langgraph.types import Command
import logging


from .prompt_loader import load_prompt_from_file, extract_system_prompt

logger = logging.getLogger(__name__)


class SetupAgent:
    """
    Vereinfachter Setup Agent - delegiert ALLE Logik an das LLM
    Nutzt NUR den Prompt aus prompt_setup_agent.md
    """
    
    def __init__(self, llm: BaseChatModel):
        self.llm = llm
        self.name = "setup_agent"
        self.system_prompt = ""
        self.load_prompt()
    
    def load_prompt(self) -> None:
        """Lädt Setup Agent Prompt aus prompts/prompt_setup_agent.md"""
        try:
            raw_content = load_prompt_from_file("prompt_setup_agent.md")
            self.system_prompt = extract_system_prompt(raw_content)
            logger.info("Setup Agent prompt successfully loaded")
        except Exception as e:
            logger.error(f"Error loading Setup Agent prompt: {e}")
            self.system_prompt = "Du bist ein Setup Agent für TextRPG."
    
    def process_message(self, messages: List[BaseMessage], state: Dict[str, Any]) -> Command[Literal["gameplay_agent"]] | str:
        """
        Einfache Message-Verarbeitung - alles durch LLM mit md-Prompt
        
        Args:
            messages: Conversation history
            state: Current state
            
        Returns:
            Command oder string response
        """
        # Bereite Messages für LLM vor
        llm_messages = [{"role": "system", "content": self.system_prompt}]
        
        # Füge Conversation History hinzu
        for msg in messages[-10:]:  # Letzte 10 Messages
            role = "user" if msg.type == "human" else "assistant"
            llm_messages.append({"role": role, "content": msg.content})
        
        # LLM-Aufruf
        response = self.llm.invoke(llm_messages)
        
        # WICHTIG: Extrahiere content als String, nicht das ganze AIMessage-Objekt!
        if hasattr(response, 'content'):
            content = str(response.content)
        else:
            content = str(response)
        
        logger.info(f"Agent response extracted: {content[:100]}...")
        
        # Erkenne Setup-Completion und erstelle Command oder return string
        return self._check_setup_complete(content, state) or content
    
    def _check_setup_complete(self, response: str, state: Dict[str, Any]) -> Optional[Command[Literal["gameplay_agent"]]]:
        """
        Prüft ob Setup abgeschlossen ist basierend auf LLM Response
        Das LLM signalisiert Completion mit [SETUP-COMPLETE]
        """
        logger.info(f"Checking for [SETUP-COMPLETE] in response: {response[:200]}...")
        
        if "[SETUP-COMPLETE]" not in response:
            logger.info("No [SETUP-COMPLETE] marker found in response")
            return None
        
        logger.info("SETUP-COMPLETE marker detected! Creating LangGraph Command...")
        
        # Extrahiere Setup-Daten aus der Response
        setup_data = self._extract_setup_data(response)
        
        # OFFIZIELLE LANGGRAPH COMMAND SYNTAX
        return Command(
            update={
                "current_agent": "gameplay_agent",
                "story_phase": "gameplay",
                "handoff_data": {
                    "type": "silent_handoff",
                    "from_agent": "setup_agent",
                    "to_agent": "gameplay_agent",
                    "handoff_data": setup_data
                },
                "chapter_count": 0,
                "interaction_count": 0
            },
            goto="gameplay_agent"
        )
    
    def _extract_setup_data(self, response: str) -> Dict[str, Any]:
        """
        Extrahiert Setup-Daten aus LLM Response
        Das LLM formatiert diese als strukturierte Daten
        """
        # Suche nach Setup-Daten Block
        import json
        import re
        
        # Versuche JSON-Block zu finden
        json_match = re.search(r'\{[^}]+\}', response)
        if json_match:
            try:
                return json.loads(json_match.group())
            except:
                pass
        
        # Fallback: Basis-Daten
        return {
            "creation_mode": "free",
            "setting": "agent_choice",
            "difficulty": "Standard"
        } 