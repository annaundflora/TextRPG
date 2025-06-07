"""
Einfacher Test für den Agent-Workflow ohne Recursion-Probleme.
"""

import asyncio
import uuid
from app.models import ChatState
from app.graph import get_phase2_workflow
import logging

logging.basicConfig(level=logging.INFO)


async def test_simple_agent_flow():
    """Testet einen einfachen Agent-Flow ohne komplexe Multi-Turn."""
    
    print("=== Simple Agent Flow Test ===\n")
    
    # Get workflow
    workflow = get_phase2_workflow()
    
    # Test 1: Story Creator Start
    print("1. Teste Story Creator Start...")
    
    session_id = str(uuid.uuid4())
    state = ChatState(session_id=session_id)
    state.last_user_message = "Erstelle eine Fantasy-Geschichte mit einem Zauberer"
    state.processing = True
    
    result = await workflow.ainvoke(state)
    
    print(f"✅ Story Creator Flow erfolgreich")
    print(f"   Messages: {len(result.get('messages', []))}")
    print(f"   Current Agent: {result.get('current_agent')}")
    print(f"   Transition Trigger: {result.get('transition_trigger')}")
    print(f"   Processing: {result.get('processing')}")
    print(f"   Last User Message: {result.get('last_user_message')}")
    
    messages = result.get('messages', [])
    if messages:
        last_msg = messages[-1]
        print(f"   Last AI Response: {last_msg.content[:150]}...")
        
    print("\n   Story Context:")
    story_context = result.get('story_context')
    if story_context:
        print(f"   {story_context[:200]}...")
    
    print("\n=== Simple Agent Flow Test abgeschlossen ===")


if __name__ == "__main__":
    asyncio.run(test_simple_agent_flow()) 