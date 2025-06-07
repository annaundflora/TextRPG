"""
Test-Skript für die Prompt-Integration.
Testet das Laden der vollständigen Prompts und deren Funktionalität.
"""

import asyncio
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from app.agents import StoryCreatorAgent, GamemasterAgent
from app.agents.prompt_loader import get_story_creator_prompt, get_gamemaster_prompt
from app.config import settings
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_prompt_loading():
    """Testet das Laden der vollständigen Prompts."""
    
    print("=== Prompt Loading Test ===\n")
    
    # Test 1: Direkte Prompt-Loader
    print("1. Teste direkte Prompt-Loader...")
    
    try:
        story_prompt = get_story_creator_prompt()
        print(f"✅ Story Creator Prompt geladen: {len(story_prompt)} Zeichen")
        print(f"   Erste 100 Zeichen: {story_prompt[:100]}...")
    except Exception as e:
        print(f"❌ Fehler beim Laden des Story Creator Prompts: {e}")
    
    try:
        gm_prompt = get_gamemaster_prompt()
        print(f"✅ Gamemaster Prompt geladen: {len(gm_prompt)} Zeichen")
        print(f"   Erste 100 Zeichen: {gm_prompt[:100]}...")
    except Exception as e:
        print(f"❌ Fehler beim Laden des Gamemaster Prompts: {e}")
    
    print("-" * 50)
    
    # Test 2: Agent-Integration
    print("\n2. Teste Agent-Integration der Prompts...")
    
    # LLM initialisieren
    llm = ChatOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=settings.openrouter_api_key,
        model=settings.llm_default
    )
    
    # Story Creator mit vollständigem Prompt
    print("\n2a. Story Creator mit vollständigem Prompt...")
    story_agent = StoryCreatorAgent(llm)
    print(f"   System Prompt Länge: {len(story_agent.system_prompt)} Zeichen")
    
    # Gamemaster mit vollständigem Prompt  
    print("\n2b. Gamemaster mit vollständigem Prompt...")
    gm_agent = GamemasterAgent(llm)
    print(f"   System Prompt Länge: {len(gm_agent.system_prompt)} Zeichen")
    
    print("-" * 50)
    
    # Test 3: Funktionstest mit vollständigen Prompts
    print("\n3. Funktionstest mit vollständigen Prompts...")
    
    # Test Story Creator  
    print("\n3a. Story Creator mit vollständigem Prompt...")
    messages = [HumanMessage(content="Erstelle ein kurzes Fantasy-Abenteuer mit einem Dieb.")]
    
    try:
        response, should_transition, trigger = story_agent.process_message(messages, {})
        print(f"✅ Story Creator Response erhalten ({len(response)} Zeichen)")
        print(f"   Transition erkannt: {should_transition}")
        print(f"   Trigger: {trigger}")
        print(f"\n   Erste 200 Zeichen:\n   {response[:200]}...")
    except Exception as e:
        print(f"❌ Fehler bei Story Creator Test: {e}")
    
    # Test Gamemaster
    print("\n3b. Gamemaster mit vollständigem Prompt...")
    messages = [HumanMessage(content="Der Spieler wählt Option 1: Schleicht sich zur Hintertür.")]
    
    try:
        response, should_transition, trigger = gm_agent.process_message(messages, {})
        print(f"✅ Gamemaster Response erhalten ({len(response)} Zeichen)")
        print(f"   Transition erkannt: {should_transition}")
        print(f"   Trigger: {trigger}")
        print(f"\n   Erste 200 Zeichen:\n   {response[:200]}...")
    except Exception as e:
        print(f"❌ Fehler bei Gamemaster Test: {e}")
    
    print("\n=== Prompt Integration Test abgeschlossen ===")


if __name__ == "__main__":
    asyncio.run(test_prompt_loading()) 