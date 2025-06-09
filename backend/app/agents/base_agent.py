from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.language_models import BaseChatModel
import logging

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstrakte Basis-Klasse für alle Agents im TextRPG System."""
    
    def __init__(self, llm: BaseChatModel, name: str):
        self.llm = llm
        self.name = name
        self.system_prompt: str = ""
        
    @abstractmethod
    def load_prompt(self) -> None:
        """Lädt den spezifischen Prompt für diesen Agent."""
        pass
    
    @abstractmethod
    def detect_transition(self, response: str) -> Tuple[bool, Optional[str]]:
        """
        Prüft ob eine Transition zu einem anderen Agent notwendig ist.
        
        Returns:
            Tuple[bool, Optional[str]]: (should_transition, transition_trigger)
        """
        pass
    
    def process_message(self, messages: list[BaseMessage], state: Dict[str, Any]) -> Tuple[str, bool, Optional[str]]:
        """
        Verarbeitet eine Nachricht und generiert eine Antwort.
        
        Returns:
            Tuple[str, bool, Optional[str]]: (response, should_transition, transition_trigger)
        """
        try:
            # System-Prompt hinzufügen
            full_messages = [
                {"role": "system", "content": self.system_prompt}
            ]
            
            # Konvertiere Messages zu dict format
            for msg in messages:
                if isinstance(msg, HumanMessage):
                    full_messages.append({"role": "user", "content": msg.content})
                elif isinstance(msg, AIMessage):
                    full_messages.append({"role": "assistant", "content": msg.content})
                elif hasattr(msg, 'type') and hasattr(msg, 'content'):
                    # Handle ChatMessage objects
                    if msg.type == "human":
                        full_messages.append({"role": "user", "content": msg.content})
                    elif msg.type == "ai":
                        full_messages.append({"role": "assistant", "content": msg.content})
                    elif msg.type == "system":
                        full_messages.append({"role": "system", "content": msg.content})
                else:
                    logger.warning(f"Unknown message type: {type(msg)}")
            
            # LLM Aufruf
            response = self.llm.invoke(full_messages)
            response_text = response.content
            
            # Transition Detection
            should_transition, transition_trigger = self.detect_transition(response_text)
            
            logger.info(f"{self.name} processed message. Transition: {should_transition}")
            
            return response_text, should_transition, transition_trigger
            
        except Exception as e:
            logger.error(f"Error in {self.name}.process_message: {str(e)}")
            raise
    
 