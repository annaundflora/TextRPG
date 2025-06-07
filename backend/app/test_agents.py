"""
Einfaches Test-Skript für die Agent-Klassen.
Kann mit `python -m app.test_agents` aus dem backend/ Verzeichnis ausgeführt werden.
"""
import asyncio
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from app.agents import StoryCreatorAgent, GamemasterAgent
from app.config import settings
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_agents():
    """Testet die grundlegende Funktionalität der Agents."""
    
    # LLM initialisieren (verwendet default model aus settings)
    llm = ChatOpenAI(
        base_url=settings.openrouter_base_url,
        api_key=settings.openrouter_api_key,
        model=settings.llm_default
    )
    
    print("=== Agent Test ===\n")
    
    # Test 1: Story Creator Agent
    print("1. Teste Story Creator Agent...")
    story_agent = StoryCreatorAgent(llm)
    
    messages = [HumanMessage(content="Starte ein Fantasy-Abenteuer mit einem Magier.")]
    response, should_transition, trigger = story_agent.process_message(messages, {})
    
    print(f"\nStory Creator Response:\n{response}")
    print(f"\nShould Transition: {should_transition}")
    print(f"Trigger: {trigger}")
    print("-" * 50)
    
    # Test 2: Gamemaster Agent
    print("\n2. Teste Gamemaster Agent...")
    gm_agent = GamemasterAgent(llm)
    
    messages = [
        HumanMessage(content="Der Spieler wählt Option 1: Den dunklen Wald betreten.")
    ]
    response, should_transition, trigger = gm_agent.process_message(messages, {})
    
    print(f"\nGamemaster Response:\n{response}")
    print(f"\nShould Transition: {should_transition}")
    print(f"Trigger: {trigger}")
    
    print("\n=== Test abgeschlossen ===")


if __name__ == "__main__":
    asyncio.run(test_agents()) 