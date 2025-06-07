"""
API Test für den Agent-Workflow über HTTP-Endpoints.
Testet den kompletten Flow: Session → Story Creator → Agent Switch.
"""

import asyncio
import httpx
import json
import time
from typing import Dict, Any

# API Base URL
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/chat"


async def test_api_agent_flow():
    """Testet den Agent-Workflow über die API-Endpoints."""
    
    print("=== API Agent Flow Test ===\n")
    
    async with httpx.AsyncClient() as client:
        
        # Test 1: Session Creation
        print("1. Teste Session Creation...")
        
        try:
            response = await client.post(f"{API_BASE}/session")
            response.raise_for_status()
            
            session_data = response.json()
            session_id = session_data["session_id"]
            
            print(f"✅ Session erfolgreich erstellt")
            print(f"   Session ID: {session_id}")
            print(f"   Status: {session_data['status']}")
            print(f"   Session Info: {session_data['session_info']}")
            
        except Exception as e:
            print(f"❌ Fehler bei Session Creation: {e}")
            return
        
        print("-" * 50)
        
        # Test 2: Non-Streaming Message (Story Creator)
        print("\n2. Teste Story Creator via Non-Streaming API...")
        
        try:
            message_data = {
                "session_id": session_id,
                "message": "Erstelle ein Fantasy-Abenteuer mit einem mutigen Ritter"
            }
            
            response = await client.post(
                f"{API_BASE}/message", 
                json=message_data
            )
            response.raise_for_status()
            
            result = response.json()
            
            print(f"✅ Story Creator Response erfolgreich")
            print(f"   Session ID: {result['session_id']}")
            print(f"   Status: {result['status']}")
            print(f"   Message Type: {result['message']['type']}")
            print(f"   Response Length: {len(result['message']['content'])}")
            print(f"   Response Preview: {result['message']['content'][:150]}...")
            
            # Check agent metadata
            if 'metadata' in result['message']:
                metadata = result['message']['metadata']
                print(f"   Agent: {metadata.get('agent', 'Unknown')}")
                print(f"   Phase: {metadata.get('phase', 'Unknown')}")
                print(f"   Should Transition: {metadata.get('should_transition', 'Unknown')}")
                print(f"   Transition Trigger: {metadata.get('transition_trigger', 'Unknown')}")
            
        except Exception as e:
            print(f"❌ Fehler bei Non-Streaming Message: {e}")
            print(f"   Response: {e.response.text if hasattr(e, 'response') else 'No response'}")
            return
        
        print("-" * 50)
        
        # Test 3: Session Info nach Agent-Processing  
        print("\n3. Teste Session Info nach Agent-Processing...")
        
        try:
            response = await client.get(f"{API_BASE}/session/{session_id}")
            response.raise_for_status()
            
            session_info = response.json()
            
            print(f"✅ Session Info erfolgreich abgerufen")
            print(f"   Session ID: {session_info['session_id']}")
            print(f"   Message Count: {len(session_info['messages'])}")
            print(f"   Active: {session_info['session_info']['active']}")
            print(f"   Processing: {session_info['session_info']['processing']}")
            
            # Check messages
            messages = session_info['messages']
            print(f"\n   Messages in Session:")
            for i, msg in enumerate(messages):
                print(f"     {i+1}. {msg['type']}: {msg['content'][:80]}...")
                if 'metadata' in msg and msg['metadata']:
                    metadata = msg['metadata']
                    agent = metadata.get('agent')
                    if agent:
                        print(f"         Agent: {agent}")
            
        except Exception as e:
            print(f"❌ Fehler bei Session Info: {e}")
            return
        
        print("-" * 50)
        
        # Test 4: Streaming API (Gamemaster Response)
        print("\n4. Teste Streaming API für Follow-up (falls Transition triggered)...")
        
        try:
            # Simulate user choosing an option
            follow_up_message = "Ich wähle Option A"
            
            stream_url = f"{API_BASE}/stream"
            params = {
                "message": follow_up_message,
                "session_id": session_id
            }
            
            print(f"   Sende Follow-up: {follow_up_message}")
            print(f"   Stream URL: {stream_url}")
            
            async with client.stream("GET", stream_url, params=params) as stream:
                stream.raise_for_status()
                
                chunks = []
                chunk_count = 0
                
                async for line in stream.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]  # Remove "data: " prefix
                        
                        if data_str == "[DONE]":
                            print(f"   Stream beendet")
                            break
                        
                        try:
                            data = json.loads(data_str)
                            chunk_count += 1
                            
                            if data.get("type") == "session_info":
                                print(f"   Session Info: {data['session_id']}")
                            
                            elif data.get("type") == "user_message":
                                print(f"   User Message bestätigt")
                            
                            elif data.get("type") == "ai_chunk":
                                chunks.append(data["content"])
                                if chunk_count <= 3:  # Show first few chunks
                                    print(f"   Chunk {data.get('chunk_id', '?')}: {data['content']}")
                            
                            elif data.get("type") == "completion":
                                print(f"   Completion: {data['total_chunks']} chunks")
                                print(f"   Response Length: {len(data['complete_response'])}")
                                print(f"   Response Preview: {data['complete_response'][:150]}...")
                            
                            elif data.get("type") == "error":
                                print(f"   ERROR: {data['error_message']}")
                                
                        except json.JSONDecodeError:
                            print(f"   Invalid JSON: {data_str}")
                
                print(f"✅ Streaming erfolgreich - {len(chunks)} chunks erhalten")
                
        except Exception as e:
            print(f"❌ Fehler bei Streaming API: {e}")
            print(f"   Details: {e.response.text if hasattr(e, 'response') else 'No response'}")
    
    print("\n=== API Agent Flow Test abgeschlossen ===")


async def test_api_server_running():
    """Testet ob der API-Server läuft."""
    
    print("=== API Server Check ===\n")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/")
            response.raise_for_status()
            
            print("✅ API Server ist erreichbar")
            return True
            
    except Exception as e:
        print(f"❌ API Server nicht erreichbar: {e}")
        print(f"   Starte den Server mit: uvicorn app.main:app --reload --port 8000")
        return False


if __name__ == "__main__":
    print("TextRPG API Agent Flow Test\n")
    
    # Check if server is running
    if asyncio.run(test_api_server_running()):
        print()
        asyncio.run(test_api_agent_flow())
    else:
        print("\nServer muss gestartet werden bevor der Test läuft!") 