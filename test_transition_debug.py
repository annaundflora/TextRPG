#!/usr/bin/env python3
"""
Debug Test für Agent-Transition
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

async def test_transition():
    """Test Agent Transition mit [SETUP-COMPLETE] Signal"""
    
    from backend.app.graph import get_session_manager
    
    print("🧪 TESTING AGENT TRANSITION")
    print("=" * 50)
    
    # Initialize
    session_manager = await get_session_manager()
    await session_manager.initialize()
    session_id = session_manager.create_session()
    
    print(f"✅ Session created: {session_id}")
    
    # Test Schritt 1: Initiale Begrüßung
    print("🔄 Step 1: Initial greeting")
    response_chunks = []
    async for chunk in session_manager.stream_process_message(session_id, "Hallo! Ich möchte ein Adventure spielen."):
        response_chunks.append(chunk)
    
    print(f"Response 1: {''.join(response_chunks)[:100]}...")
    
    # Test Schritt 2: Option A wählen
    print("\n🔄 Step 2: Choose Option A")
    response_chunks = []
    async for chunk in session_manager.stream_process_message(session_id, "A - Ich möchte eigene Vorgaben geben"):
        response_chunks.append(chunk)
    
    print(f"Response 2: {''.join(response_chunks)[:100]}...")
    
    # Test Schritt 3: Setting wählen
    print("\n🔄 Step 3: Choose Fantasy setting")
    response_chunks = []
    async for chunk in session_manager.stream_process_message(session_id, "Fantasy, wie Baldurs Gate"):
        response_chunks.append(chunk)
    
    print(f"Response 3: {''.join(response_chunks)[:100]}...")
    
    # Test Schritt 4: Schwierigkeit wählen (sollte [SETUP-COMPLETE] triggern)
    print("\n🔄 Step 4: Choose difficulty (should trigger completion)")
    response_chunks = []
    async for chunk in session_manager.stream_process_message(session_id, "Standard-Schwierigkeit bitte"):
        response_chunks.append(chunk)
    
    full_response = "".join(response_chunks)
    print(f"Response 4: {full_response[:200]}...")
    
    # Check if [SETUP-COMPLETE] appeared in response
    if "[SETUP-COMPLETE]" in full_response:
        print("✅ [SETUP-COMPLETE] found in LLM response!")
    else:
        print("❌ [SETUP-COMPLETE] NOT found in LLM response!")
    
    # Check final state
    final_state = session_manager.get_session(session_id)
    print(f"\n📊 Final State:")
    print(f"   Agent: {final_state.current_agent}")
    print(f"   Phase: {final_state.story_phase}")
    print(f"   Messages: {len(final_state.messages)}")
    
    if final_state.current_agent == "gameplay_agent":
        print("✅ TRANSITION SUCCESSFUL!")
    else:
        print("❌ TRANSITION FAILED!")
    
    return final_state.current_agent == "gameplay_agent"

if __name__ == "__main__":
    success = asyncio.run(test_transition())
    print(f"\n🎯 Result: {'SUCCESS' if success else 'FAILED'}") 