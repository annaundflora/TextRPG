"""
Test Session Tracing für LangSmith
"""

import os
import asyncio

# Set environment variables
os.environ['LANGSMITH_TRACING'] = 'true'
os.environ['LANGSMITH_API_KEY'] = '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'
os.environ['LANGSMITH_ENDPOINT'] = 'https://eu.api.smith.langchain.com'
os.environ['LANGSMITH_PROJECT'] = 'TextRPG'

from app.services.langchain_llm_service import get_langchain_llm_service
from app.models.messages import create_human_message

async def test_session_tracing():
    """Test session-level tracing"""
    
    print("🚀 Testing session-level LangSmith tracing...")
    
    llm_service = get_langchain_llm_service()
    
    # Test multiple messages in same session
    session_id = 'test-session-123'
    
    print(f"📍 Testing Session ID: {session_id}")
    
    # Message 1
    print("💬 Sending Message 1...")
    msg1 = [create_human_message('Hallo! Wie geht es dir?')]
    response1 = await llm_service.chat_completion(msg1, session_id=session_id)
    print(f"✅ Response 1: {response1.content[:50]}...")
    
    # Message 2 in same session  
    print("💬 Sending Message 2...")
    msg2 = [
        create_human_message('Hallo! Wie geht es dir?'),
        response1,
        create_human_message('Kannst du mir ein TextRPG erklären?')
    ]
    response2 = await llm_service.chat_completion(msg2, session_id=session_id)
    print(f"✅ Response 2: {response2.content[:50]}...")
    
    # Message 3 in same session
    print("💬 Sending Message 3...")
    msg3 = [
        create_human_message('Hallo! Wie geht es dir?'),
        response1,
        create_human_message('Kannst du mir ein TextRPG erklären?'),
        response2,
        create_human_message('Was ist der Unterschied zu normalen Computerspielen?')
    ]
    response3 = await llm_service.chat_completion(msg3, session_id=session_id)
    print(f"✅ Response 3: {response3.content[:50]}...")
    
    # End session
    llm_service.end_session(session_id)
    print(f"🔚 Session {session_id} ended")
    
    print("✅ Session tracing test completed!")
    print("🔍 Check LangSmith for session-grouped runs!")

if __name__ == "__main__":
    asyncio.run(test_session_tracing()) 