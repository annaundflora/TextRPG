"""
Gameplay Agent für TextRPG MVP - VEREINFACHTE VERSION
Story Creation und Gameplay ohne komplexe Pattern Matching
"""

from typing import Dict, Any, Optional, Tuple, List, Literal
from langchain_core.messages import BaseMessage, AIMessage
from langchain_core.language_models import BaseChatModel
from langgraph.types import Command
import logging

from .prompt_loader import load_prompt_from_file, extract_system_prompt

logger = logging.getLogger(__name__)


class GameplayAgent:
    """
    Vereinfachter Gameplay Agent
    - Story Generation via LLM und prompt_gameplay_agent.md
    - Keine komplexe Pattern Detection
    """
    
    def __init__(self, llm: BaseChatModel):
        self.llm = llm
        self.name = "gameplay_agent"
        self.system_prompt = ""
        self.load_prompt()
    
    def load_prompt(self) -> None:
        """Lädt Gameplay Agent Prompt aus prompts/prompt_gameplay_agent.md"""
        try:
            raw_content = load_prompt_from_file("prompt_gameplay_agent.md")
            self.system_prompt = extract_system_prompt(raw_content)
            logger.info("Gameplay Agent prompt successfully loaded")
        except Exception as e:
            logger.error(f"Error loading Gameplay Agent prompt: {e}")
            self.system_prompt = "Du bist ein Gameplay Agent für TextRPG. Erstelle eine fesselnde interaktive Geschichte."
    
    def process_message(self, messages: List[BaseMessage], state: Dict[str, Any]) -> str:
        """
        Verarbeitet Message mit LLM und Gameplay-Prompt
        
        Args:
            messages: Message history
            state: Current state with handoff_data etc.
            
        Returns:
            Story/gameplay response as string
        """
        
        # Bereite Context für LLM vor
        llm_messages = [{"role": "system", "content": self.system_prompt}]
        
        # Füge Setup-Kontext hinzu falls vorhanden
        handoff_data = state.get("handoff_data")
        if handoff_data and handoff_data.get("handoff_data"):
            setup_context = f"Setup-Kontext: {handoff_data['handoff_data']}"
            llm_messages.append({"role": "system", "content": setup_context})
        
        # Füge Message History hinzu
        for msg in messages[-10:]:  # Letzte 10 Messages
            role = "user" if msg.type == "human" else "assistant"
            llm_messages.append({"role": role, "content": msg.content})
        
        # LLM-Aufruf für Story/Gameplay
        response = self.llm.invoke(llm_messages)
        
        # WICHTIG: Extrahiere nur den content als String
        if hasattr(response, 'content'):
            content = str(response.content)
        else:
            content = str(response)
        
        logger.info(f"Gameplay agent response generated: {content[:100]}...")
        
        return content
    
 