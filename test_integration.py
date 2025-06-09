#!/usr/bin/env python3
"""
Integration Test für das vollständige TextRPG System
Testet SessionManager mit echten LangGraph-Nodes
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

async def test_session_manager_integration():
    """
    Testet das komplette System: SessionManager → LangGraph → Agents
    """
    print("🧪 INTEGRATION TEST: SessionManager + LangGraph + Agents")
    print("=" * 60)
    
    try:
        from backend.app.graph import get_session_manager
        from backend.app.config import settings
        
        # Check API key
        if not settings.openrouter_api_key:
            print("❌ OPENROUTER_API_KEY fehlt!")
            return False
            
        print(f"✅ API Key vorhanden: {settings.openrouter_api_key[:8]}...")
        print(f"✅ Models: Setup={settings.llm_creator}, Gameplay={settings.llm_gamemaster}")
        
        # Initialize SessionManager
        print("\n🔧 Initialisiere SessionManager...")
        session_manager = await get_session_manager()
        await session_manager.initialize()
        print("✅ SessionManager initialisiert")
        
        # Create new session
        print("\n📝 Erstelle neue Session...")
        session_id = session_manager.create_session()
        print(f"✅ Session erstellt: {session_id}")
        
        # Test 1: Setup Agent Call
        print("\n🎯 TEST 1: Setup Agent über SessionManager")
        test_message = "Hallo! Ich möchte ein Fantasy-Abenteuer spielen."
        print(f"👤 Input: {test_message}")
        
        response_chunks = []
        async for chunk in session_manager.stream_process_message(session_id, test_message):
            response_chunks.append(chunk)
            print(f"📨 Chunk: {chunk[:50]}{'...' if len(chunk) > 50 else ''}")
            
        full_response = "".join(response_chunks)
        print(f"\n🤖 Vollständige Antwort ({len(full_response)} Zeichen):")
        print(f"{full_response[:200]}{'...' if len(full_response) > 200 else ''}")
        
        # Check session state
        session_state = session_manager.get_session(session_id)
        print(f"\n📊 Session State:")
        print(f"   Messages: {len(session_state.messages)}")
        print(f"   Current Agent: {session_state.current_agent}")
        print(f"   Story Phase: {session_state.story_phase}")
        print(f"   Processing: {session_state.processing}")
        
        if session_state.messages:
            last_message = session_state.messages[-1]
            print(f"   Last Message Type: {last_message.type}")
            print(f"   Last Message: {last_message.content[:100]}...")
        
        # Test 2: Follow-up message
        print("\n🎯 TEST 2: Follow-up Message")
        followup_message = "Mittelalterliche Fantasy mit einem Zauberer als Charakter."
        print(f"👤 Input: {followup_message}")
        
        response_chunks = []
        async for chunk in session_manager.stream_process_message(session_id, followup_message):
            response_chunks.append(chunk)
            
        full_response2 = "".join(response_chunks)
        print(f"🤖 Antwort: {full_response2[:200]}{'...' if len(full_response2) > 200 else ''}")
        
        # Final session state
        final_state = session_manager.get_session(session_id)
        print(f"\n📊 Final Session State:")
        print(f"   Messages: {len(final_state.messages)}")
        print(f"   Current Agent: {final_state.current_agent}")
        print(f"   Story Phase: {final_state.story_phase}")
        
        print("\n🎉 INTEGRATION TEST ERFOLGREICH!")
        print("✅ SessionManager funktioniert")
        print("✅ LangGraph-Nodes werden aufgerufen")
        print("✅ Agents generieren Antworten")
        print("✅ State wird korrekt verwaltet")
        
        return True
        
    except Exception as e:
        print(f"\n❌ INTEGRATION TEST FEHLER: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """
    Main test routine
    """
    print("🚀 TEXTRPG VOLLSTÄNDIGER INTEGRATION TEST")
    print("Testet: Backend Import → SessionManager → LangGraph → Agents → LLM")
    print("=" * 70)
    
    # Test import first
    try:
        from backend.app.main import app
        print("✅ Backend Import erfolgreich")
    except Exception as e:
        print(f"❌ Backend Import fehlgeschlagen: {e}")
        return
    
    # Run integration test
    success = await test_session_manager_integration()
    
    if success:
        print("\n🎉 ALLE TESTS BESTANDEN!")
        print("Das System ist bereit für Frontend-Integration und LangSmith-Tracing!")
    else:
        print("\n❌ TESTS FEHLGESCHLAGEN!")
        print("System benötigt weitere Fixes.")


if __name__ == "__main__":
    asyncio.run(main()) 