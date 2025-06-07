"""
Debug Script für Story Creator Agent
Test des Message-Processing und LLM-Integration
"""

import asyncio
from langchain_openai import ChatOpenAI
from agents.story_creator import StoryCreatorAgent
from models import create_human_message, create_ai_message
from config import settings


async def debug_story_creator():
    """Debug Story Creator Agent Verhalten"""
    
    print("🔍 Story Creator Debug Test\n")
    
    # Initialize LLM
    llm = ChatOpenAI(
        base_url=settings.openrouter_base_url,
        api_key=settings.openrouter_api_key,
        model=settings.llm_creator,
        temperature=0.7
    )
    
    # Create agent
    agent = StoryCreatorAgent(llm)
    
    print(f"✅ Agent erstellt mit Model: {settings.llm_creator}")
    print(f"📖 System Prompt Länge: {len(agent.system_prompt)} Zeichen")
    print(f"📖 System Prompt Preview: {agent.system_prompt[:200]}...\n")
    
    # Test 1: Initiale Session (leer)
    print("🎯 TEST 1: Initiale Session (keine Messages)")
    messages_1 = []
    state_1 = {}
    
    try:
        response_1, should_transition_1, trigger_1 = agent.process_message(messages_1, state_1)
        print(f"✅ Response: {response_1[:200]}...")
        print(f"🔄 Should Transition: {should_transition_1}")
        print(f"🎲 Transition Trigger: {trigger_1}\n")
    except Exception as e:
        print(f"❌ Error in Test 1: {e}\n")
    
    # Test 2: Nach User-Antwort "Option A"
    print("🎯 TEST 2: User wählt Option A")
    messages_2 = [
        create_ai_message(
            "Willkommen! Ich erstelle für dich ein spannendes Adventure für dein TextRPG.\n\n"
            "Möchtest du:\nA) Mir eigene Vorgaben geben (Setting, Charaktere, Thema, etc.)\n"
            "B) Mich komplett frei eine Geschichte entwickeln lassen\n\nWas bevorzugst du?"
        ),
        create_human_message("Ich wähle Option A - ich möchte eigene Vorgaben geben")
    ]
    state_2 = {}
    
    try:
        response_2, should_transition_2, trigger_2 = agent.process_message(messages_2, state_2)
        print(f"✅ Response: {response_2[:300]}...")
        print(f"🔄 Should Transition: {should_transition_2}")
        print(f"🎲 Transition Trigger: {trigger_2}\n")
    except Exception as e:
        print(f"❌ Error in Test 2: {e}\n")
    
    # Test 3: User gibt Vorgaben
    print("🎯 TEST 3: User gibt konkrete Vorgaben")
    messages_3 = [
        create_ai_message(
            "Willkommen! Ich erstelle für dich ein spannendes Adventure für dein TextRPG.\n\n"
            "Möchtest du:\nA) Mir eigene Vorgaben geben (Setting, Charaktere, Thema, etc.)\n"
            "B) Mich komplett frei eine Geschichte entwickeln lassen\n\nWas bevorzugst du?"
        ),
        create_human_message("Ich wähle Option A - ich möchte eigene Vorgaben geben"),
        create_ai_message("Perfekt! Erzähle mir deine Vorgaben - welches Setting, welche Charaktere oder Themen stellst du dir vor?"),
        create_human_message(
            "Fantasy-Setting, mittelalterliche Welt mit Magie. "
            "Ich spiele einen jungen Magier namens Eldric. "
            "Es geht um die Suche nach einem verschwundenen Artefakt."
        )
    ]
    state_3 = {}
    
    try:
        response_3, should_transition_3, trigger_3 = agent.process_message(messages_3, state_3)
        print(f"✅ Response: {response_3[:400]}...")
        print(f"🔄 Should Transition: {should_transition_3}")
        print(f"🎲 Transition Trigger: {trigger_3}")
        
        # Check für Handlungsoptionen
        has_handlungsoptionen = "--- HANDLUNGSOPTIONEN ---" in response_3
        print(f"🎲 Hat Handlungsoptionen: {has_handlungsoptionen}")
        
        # Debug: Welcher adaptive Prompt wurde verwendet?
        used_prompt = agent.get_adaptive_system_prompt(messages_3, state_3)
        print(f"🔍 Adaptiver Prompt Used: {used_prompt[:100]}...")
        print()
        
    except Exception as e:
        print(f"❌ Error in Test 3: {e}\n")
    
    # Test Message Format Debug
    print("🔍 MESSAGE FORMAT DEBUG:")
    print("Expected Format:")
    print('{"role": "system", "content": "..."}')
    print('{"role": "user", "content": "..."}')
    print('{"role": "assistant", "content": "..."}')
    
    print("\nActual Format für Test 3:")
    full_messages = [{"role": "system", "content": agent.system_prompt[:100] + "..."}]
    for msg in messages_3[-2:]:  # Nur die letzten 2 Messages
        if msg.type == "human":
            full_messages.append({"role": "user", "content": msg.content})
        elif msg.type == "ai":
            full_messages.append({"role": "assistant", "content": msg.content})
    
    for i, msg in enumerate(full_messages):
        print(f"{i+1}. {msg['role']}: {msg['content'][:100]}...")


if __name__ == "__main__":
    asyncio.run(debug_story_creator()) 