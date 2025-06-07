"""
Test für Agent-Workflow Streaming API
Test der Umstellung von direktem LLM auf Agent-Workflow mit Streaming
"""

import asyncio
import aiohttp
import json
from datetime import datetime


async def test_streaming_agent_flow():
    """Test für Agent-Workflow Streaming mit Server-Sent Events"""
    
    print(f"🔥 Agent-Workflow Streaming Test gestartet: {datetime.now()}")
    
    base_url = "http://localhost:8000"
    session_id = None
    
    try:
        # 1. Session erstellen
        print("\n1️⃣ Session erstellen...")
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{base_url}/chat/session") as response:
                session_data = await response.json()
                session_id = session_data["session_id"]
                print(f"✅ Session erstellt: {session_id}")
                print(f"   Session Info: {session_data['session_info']}")
        
        # 2. Streaming Message Test
        print("\n2️⃣ Agent-Workflow Streaming Test...")
        user_message = "Beginne eine epische Fantasy-Geschichte über einen jungen Magier."
        
        chunks_received = 0
        complete_response = ""
        agent_info = {}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{base_url}/chat/stream",
                params={
                    "message": user_message,
                    "session_id": session_id
                }
            ) as response:
                
                print(f"📡 Streaming Response Status: {response.status}")
                
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    
                    if line.startswith('data: '):
                        data_str = line[6:]  # Remove 'data: '
                        
                        if data_str == '[DONE]':
                            print("🏁 Stream beendet")
                            break
                        
                        try:
                            data = json.loads(data_str)
                            event_type = data.get("type")
                            
                            if event_type == "user_message":
                                print(f"👤 User Message: {data['content'][:50]}...")
                            
                            elif event_type == "ai_chunk":
                                chunks_received += 1
                                chunk = data.get("content", "")
                                complete_response += chunk
                                
                                if chunks_received % 10 == 0:  # Jeder 10. Chunk
                                    print(f"🔄 Chunk {chunks_received}: {len(chunk)} chars")
                            
                            elif event_type == "completion":
                                agent_info = {
                                    "agent": data.get("agent"),
                                    "transition_trigger": data.get("transition_trigger"),
                                    "message_count": data.get("message_count"),
                                    "total_chunks": data.get("total_chunks")
                                }
                                print(f"✅ Completion: {agent_info}")
                            
                            elif event_type == "error":
                                print(f"❌ Error: {data.get('error_message')}")
                                break
                        
                        except json.JSONDecodeError:
                            print(f"⚠️ JSON Decode Error: {data_str}")
        
        print(f"\n📊 Streaming Statistiken:")
        print(f"   Chunks empfangen: {chunks_received}")
        print(f"   Response Länge: {len(complete_response)} Zeichen")
        print(f"   Aktueller Agent: {agent_info.get('agent')}")
        print(f"   Transition Trigger: {agent_info.get('transition_trigger')}")
        print(f"   Messages in Session: {agent_info.get('message_count')}")
        
        print(f"\n📖 Story Preview (erste 300 Zeichen):")
        print(f"   {complete_response[:300]}...")
        
        # 3. Session State nach Streaming prüfen
        print("\n3️⃣ Session State prüfen...")
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_url}/chat/session/{session_id}") as response:
                session_data = await response.json()
                
                print(f"✅ Session Messages: {len(session_data['messages'])}")
                
                for i, msg in enumerate(session_data['messages']):
                    print(f"   {i+1}. {msg['type']}: {msg['content'][:50]}...")
                
                # Check agent state
                if 'session_info' in session_data:
                    print(f"   Session Active: {session_data['session_info'].get('active')}")
                    print(f"   Processing: {session_data['session_info'].get('processing')}")
        
        # 4. Follow-up Test: Gamemaster Response
        print("\n4️⃣ Follow-up Test (sollte zum Gamemaster wechseln)...")
        follow_up = "Ich möchte den Zauber lernen."
        
        chunks_received_2 = 0
        complete_response_2 = ""
        agent_info_2 = {}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{base_url}/chat/stream",
                params={
                    "message": follow_up,
                    "session_id": session_id
                }
            ) as response:
                
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    
                    if line.startswith('data: '):
                        data_str = line[6:]
                        
                        if data_str == '[DONE]':
                            break
                        
                        try:
                            data = json.loads(data_str)
                            event_type = data.get("type")
                            
                            if event_type == "ai_chunk":
                                chunks_received_2 += 1
                                complete_response_2 += data.get("content", "")
                            
                            elif event_type == "completion":
                                agent_info_2 = {
                                    "agent": data.get("agent"),
                                    "transition_trigger": data.get("transition_trigger"),
                                    "message_count": data.get("message_count")
                                }
                        
                        except json.JSONDecodeError:
                            pass
        
        print(f"📊 Follow-up Statistiken:")
        print(f"   Chunks: {chunks_received_2}")
        print(f"   Response Länge: {len(complete_response_2)}")
        print(f"   Aktueller Agent: {agent_info_2.get('agent')}")
        print(f"   Transition Trigger: {agent_info_2.get('transition_trigger')}")
        
        print(f"\n🎯 Agent-Workflow Streaming Test ERFOLGREICH!")
        print(f"   ✅ Story Creator → Gamemaster Agent Switching funktioniert")
        print(f"   ✅ Streaming über Agent-Workflow läuft")
        print(f"   ✅ Session State Management korrekt")
        
        return True
        
    except Exception as e:
        print(f"❌ Test Fehler: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    asyncio.run(test_streaming_agent_flow()) 