#!/usr/bin/env python3
"""
Test für [SETUP-COMPLETE] Transition Problem
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

async def test_setup_complete_transition():
    """Test was nach [SETUP-COMPLETE] passiert"""
    
    from backend.app.graph import get_session_manager
    
    print("🧪 SETUP-COMPLETE TRANSITION TEST")
    print("=" * 50)
    
    # Initialize
    session_manager = await get_session_manager()
    await session_manager.initialize()
    session_id = session_manager.create_session()
    
    print(f"✅ Session created: {session_id}")
    
    # Schnell zum [SETUP-COMPLETE] kommen
    print("\n📝 Message 1: Initiale Begrüßung")
    async for chunk in session_manager.stream_process_message(session_id, "Hi"):
        pass  # Ignore output
    
    print("📝 Message 2: Option B wählen")
    async for chunk in session_manager.stream_process_message(session_id, "B"):
        pass
    
    print("📝 Message 3: Keine Ausschlüsse")
    response_chunks = []
    async for chunk in session_manager.stream_process_message(session_id, "nein"):
        response_chunks.append(chunk)
    
    response = "".join(response_chunks)
    print(f"🤖 Setup Complete Response: {response}")
    
    # Check state NACH [SETUP-COMPLETE]
    state_after_complete = session_manager.get_session(session_id)
    print(f"\n📊 State NACH [SETUP-COMPLETE]:")
    print(f"   Agent: {state_after_complete.current_agent}")
    print(f"   Phase: {state_after_complete.story_phase}")
    print(f"   Messages: {len(state_after_complete.messages)}")
    print(f"   Handoff Data: {state_after_complete.handoff_data}")
    
    # JETZT: Was passiert wenn User eine weitere Message sendet?
    print(f"\n📝 Message 4: User fordert Story-Start")
    response_chunks = []
    async for chunk in session_manager.stream_process_message(session_id, "Start die Geschichte bitte"):
        response_chunks.append(chunk)
    
    story_response = "".join(response_chunks)
    print(f"🤖 Story Response: {story_response[:200]}...")
    
    # Check final state
    final_state = session_manager.get_session(session_id)
    print(f"\n📊 Final State:")
    print(f"   Agent: {final_state.current_agent}")
    print(f"   Phase: {final_state.story_phase}")
    
    # ANALYSE
    if "[SETUP-COMPLETE]" in response:
        print("✅ [SETUP-COMPLETE] wird gesendet")
    else:
        print("❌ [SETUP-COMPLETE] wird NICHT gesendet")
    
    if state_after_complete.current_agent == "gameplay_agent":
        print("✅ Transition zum Gameplay Agent erfolgt")
    else:
        print("❌ Transition zum Gameplay Agent FEHLGESCHLAGEN")
    
    if final_state.current_agent == "gameplay_agent":
        print("✅ Gameplay Agent ist aktiv")
        if "Du findest dich" in story_response or "Das Abenteuer beginnt" in story_response:
            print("✅ Geschichte wurde gestartet")
            return True
        else:
            print("❌ Geschichte wurde NICHT gestartet")
            return False
    else:
        print("❌ Setup Agent ist IMMER NOCH aktiv")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_setup_complete_transition())
    print(f"\n🎯 Result: {'SUCCESS' if success else 'FAILED'}") 