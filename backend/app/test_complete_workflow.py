"""
Vollständiger Agent-Workflow Test
Test der kompletten Session von Setup bis Gamemaster-Übergang
"""

import asyncio
import aiohttp
import json
from datetime import datetime


async def test_complete_agent_workflow():
    """Test der kompletten Agent Session: Setup → Story → Gamemaster"""
    
    print(f"🎯 Vollständiger Agent-Workflow Test gestartet: {datetime.now()}")
    
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
        
        # 2. Setup-Phase: User wählt Option A
        print("\n2️⃣ Setup-Phase: User wählt Option A...")
        setup_response = await send_message_api(base_url, session_id, "Ich wähle Option A - ich möchte eigene Vorgaben geben")
        print(f"📖 Story Creator Antwort: {setup_response[:200]}...")
        
        # Check ob noch bei Story Creator
        agent_info = await get_session_info(base_url, session_id)
        current_agent = None
        for msg in agent_info['messages']:
            if msg['type'] == 'ai' and 'agent' in msg.get('metadata', {}):
                current_agent = msg['metadata']['agent']
        
        print(f"🤖 Aktueller Agent nach Setup: {current_agent}")
        
        # 3. Vorgaben geben
        print("\n3️⃣ User gibt Vorgaben...")
        vorgaben = """Ich möchte ein Fantasy-Abenteuer mit folgenden Vorgaben:
        - Setting: Mittelalterliche Welt mit Magie
        - Charakter: Ein junger Magier namens Eldric
        - Thema: Die Suche nach einem verschwundenen Artefakt
        - Stil: Episch und abenteuerlich"""
        
        story_response = await send_message_api(base_url, session_id, vorgaben)
        print(f"📖 Story Creator erstellt Abenteuer ({len(story_response)} Zeichen)")
        print(f"Story Preview: {story_response[:300]}...")
        
        # Check auf Handlungsoptionen
        has_handlungsoptionen = "--- HANDLUNGSOPTIONEN ---" in story_response
        print(f"🎲 Handlungsoptionen gefunden: {has_handlungsoptionen}")
        
        # 4. Session State nach Story-Erstellung prüfen
        print("\n4️⃣ Session State nach Story-Erstellung...")
        agent_info = await get_session_info(base_url, session_id)
        current_agent = None
        transition_trigger = None
        
        for msg in agent_info['messages']:
            if msg['type'] == 'ai' and 'agent' in msg.get('metadata', {}):
                current_agent = msg['metadata']['agent']
                if 'transition_trigger' in msg.get('metadata', {}):
                    transition_trigger = msg['metadata']['transition_trigger']
        
        print(f"🤖 Aktueller Agent: {current_agent}")
        print(f"🔄 Transition Trigger: {transition_trigger}")
        print(f"📝 Total Messages: {len(agent_info['messages'])}")
        
        # 5. User wählt Handlungsoption (sollte zum Gamemaster gehen)
        print("\n5️⃣ User wählt Handlungsoption...")
        if has_handlungsoptionen:
            action_response = await send_message_api(base_url, session_id, "Ich untersuche die mysteriösen Runen genauer")
            print(f"🎲 Gamemaster Antwort ({len(action_response)} Zeichen)")
            print(f"Gamemaster Preview: {action_response[:300]}...")
            
            # Check Agent nach Aktion
            agent_info = await get_session_info(base_url, session_id)
            final_agent = None
            
            for msg in agent_info['messages']:
                if msg['type'] == 'ai' and 'agent' in msg.get('metadata', {}):
                    final_agent = msg['metadata']['agent']
            
            print(f"🤖 Finaler Agent: {final_agent}")
            
            # Erwartetes Ergebnis
            if final_agent == "gamemaster":
                print("✅ ERFOLG: Korrekte Transition Story Creator → Gamemaster")
            else:
                print(f"❌ FEHLER: Erwartete 'gamemaster', aber Agent ist '{final_agent}'")
        else:
            print("⚠️ Keine Handlungsoptionen gefunden - Story Creator sollte diese erstellen")
        
        # 6. Finaler Session Report
        print("\n6️⃣ Finaler Session Report...")
        final_info = await get_session_info(base_url, session_id)
        print(f"📊 Total Messages: {len(final_info['messages'])}")
        
        agent_sequence = []
        for msg in final_info['messages']:
            if msg['type'] == 'ai' and 'agent' in msg.get('metadata', {}):
                agent_sequence.append(msg['metadata']['agent'])
        
        print(f"🔄 Agent Sequence: {' → '.join(agent_sequence)}")
        
        # Erwartete Sequence: story_creator → story_creator → gamemaster
        expected_sequence = ["story_creator", "story_creator", "gamemaster"]
        if agent_sequence == expected_sequence:
            print("✅ PERFEKTER WORKFLOW: Setup → Story → Gamemaster")
        else:
            print(f"❌ WORKFLOW PROBLEM: Erwartet {expected_sequence}, erhalten {agent_sequence}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test Fehler: {e}")
        import traceback
        traceback.print_exc()
        return False


async def send_message_api(base_url: str, session_id: str, message: str) -> str:
    """Sende Message via API und return Antwort"""
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{base_url}/chat/message",
            json={"message": message, "session_id": session_id}
        ) as response:
            data = await response.json()
            return data["message"]["content"]


async def get_session_info(base_url: str, session_id: str) -> dict:
    """Hole Session-Informationen"""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{base_url}/chat/session/{session_id}") as response:
            return await response.json()


if __name__ == "__main__":
    asyncio.run(test_complete_agent_workflow()) 