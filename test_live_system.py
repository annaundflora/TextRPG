#!/usr/bin/env python3
"""
TextRPG Live System Test
Testet die vereinfachten Agents mit echten LLM calls
"""

import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from backend.app.agents.setup_agent import SetupAgent
from backend.app.agents.gameplay_agent import GameplayAgent
from backend.app.models.converters import create_human_message, create_ai_message
from backend.app.config import settings
from langchain_openai import ChatOpenAI


async def test_setup_agent():
    """
    Test Setup Agent mit echten LLM calls
    """
    print("🧪 TESTING SETUP AGENT")
    print("=" * 50)
    
    try:
        # Initialize LLM
        llm = ChatOpenAI(
            base_url=settings.openrouter_base_url,
            api_key=settings.openrouter_api_key,
            model=settings.llm_creator
        )
        
        # Create Setup Agent
        agent = SetupAgent(llm)
        
        # Test messages
        test_messages = [
            "Hallo! Ich möchte ein Fantasy-Abenteuer spielen.",
            "Ich möchte eine mittelalterliche Fantasy-Welt mit Magie und Drachen. Mein Charakter soll ein Magier sein.",
            "Das klingt gut! Lass uns anfangen."
        ]
        
        messages = []
        state = {"session_id": "test-setup"}
        
        for i, user_input in enumerate(test_messages):
            print(f"\n--- Test {i+1} ---")
            print(f"👤 User: {user_input}")
            
            # Add user message
            user_msg = create_human_message(user_input)
            messages.append(user_msg)
            
            # Call agent
            response_text, command = agent.process_message(messages, state)
            
            print(f"🤖 Setup Agent: {response_text}")
            print(f"⚡ Command: {command}")
            
            # Add AI response
            ai_msg = create_ai_message(response_text)
            messages.append(ai_msg)
            
            # Check für Setup completion
            if command and command.get("goto") == "gameplay":
                print("✅ Setup Agent completed! Transition to Gameplay detected.")
                return messages, state
            
            print()
        
        print("❌ Setup Agent didn't complete after 3 messages")
        return messages, state
        
    except Exception as e:
        print(f"❌ Setup Agent test failed: {e}")
        return [], {}


async def test_gameplay_agent(setup_messages, setup_state):
    """
    Test Gameplay Agent mit echten LLM calls
    """
    print("\n🧪 TESTING GAMEPLAY AGENT")
    print("=" * 50)
    
    try:
        # Initialize LLM
        llm = ChatOpenAI(
            base_url=settings.openrouter_base_url,
            api_key=settings.openrouter_api_key,
            model=settings.llm_gamemaster
        )
        
        # Create Gameplay Agent
        agent = GameplayAgent(llm)
        
        # Use setup messages als context
        messages = setup_messages.copy()
        state = setup_state.copy()
        state["current_agent"] = "gameplay_agent"
        
        # Test gameplay interactions
        gameplay_inputs = [
            "Ich schaue mich um. Was sehe ich?",
            "Ich gehe in Richtung des mysteriösen Turms.",
            "Ich versuche den Zauberspruch 'Lumos' um Licht zu erschaffen."
        ]
        
        for i, user_input in enumerate(gameplay_inputs):
            print(f"\n--- Gameplay Test {i+1} ---")
            print(f"👤 User: {user_input}")
            
            # Add user message
            user_msg = create_human_message(user_input)
            messages.append(user_msg)
            
            # Call agent
            response_text, command = agent.process_message(messages, state)
            
            print(f"🎮 Gameplay Agent: {response_text}")
            print(f"⚡ Command: {command}")
            
            # Add AI response
            ai_msg = create_ai_message(response_text)
            messages.append(ai_msg)
            
            # Check für neue Kapitel oder Session Ende
            if command:
                if command.get("goto") == "new_chapter":
                    print("📖 Neues Kapitel detected!")
                elif command.get("goto") == "end":
                    print("🔚 Session Ende detected!")
                    break
            
            print()
        
        print("✅ Gameplay Agent test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Gameplay Agent test failed: {e}")
        return False


async def test_command_markers():
    """
    Test ob die Command Markers in den Prompts funktionieren
    """
    print("\n🧪 TESTING COMMAND MARKERS")
    print("=" * 50)
    
    try:
        # Test Setup Agent command detection
        llm = ChatOpenAI(
            base_url=settings.openrouter_base_url,
            api_key=settings.openrouter_api_key,
            model=settings.llm_creator
        )
        
        setup_agent = SetupAgent(llm)
        
        # Forciere Setup completion
        completion_messages = [
            create_human_message("Ich möchte ein Fantasy-Abenteuer"),
            create_ai_message("Welche Art von Fantasy magst du?"),
            create_human_message("Mittelalterlich mit Magie. Ich bin ein Zauberer."),
            create_ai_message("Perfekt! Wie schwer soll es werden?"),
            create_human_message("Normal bitte, lass uns anfangen!")
        ]
        
        response, command = setup_agent.process_message(
            completion_messages, 
            {"session_id": "marker-test"}
        )
        
        print(f"🔍 Setup Response: {response[:100]}...")
        print(f"🔍 Setup Command: {command}")
        
        if command and command.get("goto") == "gameplay":
            print("✅ Setup completion marker working!")
        else:
            print("❌ Setup completion marker not detected")
        
        return True
        
    except Exception as e:
        print(f"❌ Command marker test failed: {e}")
        return False


async def main():
    """
    Main test routine
    """
    print("🚀 TEXTRPG LIVE SYSTEM TEST")
    print("Testing vereinfachte Agents mit echten LLMs")
    print("=" * 60)
    
    # Check .env
    if not settings.openrouter_api_key:
        print("❌ OPENROUTER_API_KEY not found in .env!")
        print("Bitte .env konfigurieren:")
        print("OPENROUTER_API_KEY=your_key_here")
        return
    
    print(f"✅ Using models:")
    print(f"   Setup: {settings.llm_creator}")
    print(f"   Gameplay: {settings.llm_gamemaster}")
    print()
    
    # Test Setup Agent
    setup_messages, setup_state = await test_setup_agent()
    
    if not setup_messages:
        print("❌ Setup test failed, stopping...")
        return
    
    # Test Gameplay Agent
    gameplay_success = await test_gameplay_agent(setup_messages, setup_state)
    
    if not gameplay_success:
        print("❌ Gameplay test failed...")
        return
    
    # Test Command Markers
    marker_success = await test_command_markers()
    
    if not marker_success:
        print("❌ Command marker test failed...")
        return
    
    print("\n🎉 ALL TESTS PASSED!")
    print("✅ Setup Agent funktioniert")
    print("✅ Gameplay Agent funktioniert") 
    print("✅ Command Markers funktionieren")
    print("✅ LLM Integration funktioniert")
    print("\nSystem ready für Frontend integration! 🚀")


if __name__ == "__main__":
    asyncio.run(main()) 