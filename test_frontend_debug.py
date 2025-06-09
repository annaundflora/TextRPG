#!/usr/bin/env python3
"""
Frontend Debug Test - Simuliert exakt die User-Unterhaltung
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

async def test_user_conversation():
    """Simuliert die exakte User-Unterhaltung um Bugs zu identifizieren"""
    
    from backend.app.graph import get_session_manager
    
    print("🧪 FRONTEND DEBUG TEST")
    print("Simuliert exakt die User-Unterhaltung")
    print("=" * 60)
    
    # Initialize
    session_manager = await get_session_manager()
    await session_manager.initialize()
    session_id = session_manager.create_session()
    
    print(f"✅ Session created: {session_id}")
    
    # Message 1: User sagt "Hi"
    print("\n📝 Message 1: User sagt 'Hi'")
    response_chunks = []
    async for chunk in session_manager.stream_process_message(session_id, "Hi"):
        response_chunks.append(chunk)
    
    response1 = "".join(response_chunks)
    print(f"🤖 Response 1: {response1[:100]}...")
    
    # Check session state after message 1
    state1 = session_manager.get_session(session_id)
    print(f"📊 State 1: Agent={state1.current_agent}, Phase={state1.story_phase}, Messages={len(state1.messages)}")
    
    # Message 2: User sagt "B Komplett frei bitte"
    print("\n📝 Message 2: User sagt 'B Komplett frei bitte'")
    response_chunks = []
    async for chunk in session_manager.stream_process_message(session_id, "B Komplett frei bitte"):
        response_chunks.append(chunk)
    
    response2 = "".join(response_chunks)
    print(f"🤖 Response 2: {response2[:100]}...")
    
    # Check if this is a duplicate
    if response1[:50] == response2[:50]:
        print("🚨 DUPLICATE RESPONSE DETECTED!")
    
    # Check session state after message 2
    state2 = session_manager.get_session(session_id)
    print(f"📊 State 2: Agent={state2.current_agent}, Phase={state2.story_phase}, Messages={len(state2.messages)}")
    
    # Message 3: User sagt "B"
    print("\n📝 Message 3: User sagt 'B'")
    response_chunks = []
    async for chunk in session_manager.stream_process_message(session_id, "B"):
        response_chunks.append(chunk)
    
    response3 = "".join(response_chunks)
    print(f"🤖 Response 3: {response3[:100]}...")
    
    # Message 4: User sagt "B bedeutetd du entscheidest alles!"
    print("\n📝 Message 4: User sagt 'B bedeutetd du entscheidest alles!'")
    response_chunks = []
    async for chunk in session_manager.stream_process_message(session_id, "B bedeutetd du entscheidest alles!"):
        response_chunks.append(chunk)
    
    response4 = "".join(response_chunks)
    print(f"🤖 Response 4: {response4[:100]}...")
    
    # Check if this is the same question again
    if "Genres oder Themen" in response3 and "Genres oder Themen" in response4:
        print("🚨 AGENT IGNORES USER INPUT - SAME QUESTION TWICE!")
    
    # Message 5: User sagt "nein"
    print("\n📝 Message 5: User sagt 'nein'")
    response_chunks = []
    async for chunk in session_manager.stream_process_message(session_id, "nein"):
        response_chunks.append(chunk)
    
    response5 = "".join(response_chunks)
    print(f"🤖 Response 5: {response5[:100]}...")
    
    # Check if [SETUP-COMPLETE] was sent
    if "[SETUP-COMPLETE]" in response5:
        print("✅ [SETUP-COMPLETE] found!")
    else:
        print("❌ [SETUP-COMPLETE] NOT found!")
    
    # Final state check
    final_state = session_manager.get_session(session_id)
    print(f"\n📊 Final State:")
    print(f"   Agent: {final_state.current_agent}")
    print(f"   Phase: {final_state.story_phase}")
    print(f"   Messages: {len(final_state.messages)}")
    
    # Test next message after [SETUP-COMPLETE]
    print("\n📝 Message 6: User sagt 'Los gehts!'")
    response_chunks = []
    async for chunk in session_manager.stream_process_message(session_id, "Los gehts!"):
        response_chunks.append(chunk)
    
    response6 = "".join(response_chunks)
    print(f"🤖 Response 6: {response6[:100]}...")
    
    # Check if we're now on gameplay agent
    final_final_state = session_manager.get_session(session_id)
    print(f"\n📊 After Story Start:")
    print(f"   Agent: {final_final_state.current_agent}")
    print(f"   Phase: {final_final_state.story_phase}")
    
    if final_final_state.current_agent == "gameplay_agent":
        print("✅ TRANSITION TO GAMEPLAY SUCCESSFUL!")
        return True
    else:
        print("❌ STILL STUCK ON SETUP AGENT!")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_user_conversation())
    print(f"\n🎯 Result: {'SUCCESS' if success else 'FAILED'}") 