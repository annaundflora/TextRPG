"""
Test-Skript für das erweiterte Agent-State Management.
Testet die neuen Agent-Management Funktionalitäten in ChatState.
"""

from app.models.state import ChatState, AgentType, SessionInfo
from app.models.messages import ChatMessage
import uuid
from datetime import datetime


def test_agent_state_management():
    """Testet die Agent-Management Funktionalitäten des ChatState."""
    
    print("=== Agent State Management Test ===\n")
    
    # Test 1: Basic State Creation
    print("1. Basic State Creation...")
    session_id = str(uuid.uuid4())
    state = ChatState(session_id=session_id)
    
    print(f"✅ ChatState erstellt mit Session ID: {session_id}")
    print(f"   Initial Agent: {state.current_agent}")
    print(f"   Initial Trigger: {state.transition_trigger}")
    print(f"   Initial Story Context: {state.story_context}")
    print(f"   Initial Character Info: {state.character_info}")
    print()
    
    # Test 2: Agent Switching
    print("2. Agent Switching...")
    
    # Switch zu Story Creator
    state.switch_agent(
        new_agent="story_creator",
        trigger="session_start",
        handoff_context="Neue Session gestartet"
    )
    
    print(f"✅ Agent-Switch zu Story Creator")
    print(f"   Current Agent: {state.current_agent}")
    print(f"   Transition Trigger: {state.transition_trigger}")
    print(f"   Handoff Context: {state.agent_handoff_context}")
    print()
    
    # Switch zu Gamemaster
    state.switch_agent(
        new_agent="gamemaster", 
        trigger="handlungsoptionen_präsentiert",
        handoff_context="Spieler soll Handlungsoption wählen"
    )
    
    print(f"✅ Agent-Switch zu Gamemaster")
    print(f"   Current Agent: {state.current_agent}")
    print(f"   Transition Trigger: {state.transition_trigger}")
    print(f"   Handoff Context: {state.agent_handoff_context}")
    print()
    
    # Test 3: Context Management
    print("3. Context Management...")
    
    # Story Context
    story_context = "Der Spieler ist ein Dieb in einer mittelalterlichen Stadt."
    state.update_story_context(story_context)
    print(f"✅ Story Context gesetzt: {state.story_context[:50]}...")
    
    # Character Info
    character_updates = {
        "name": "Elara",
        "class": "Dieb",
        "level": 3,
        "skills": ["Schleichen", "Schlösser knacken"],
        "current_location": "Marktplatz"
    }
    state.update_character_info(character_updates)
    print(f"✅ Character Info gesetzt: {len(state.character_info)} Felder")
    print(f"   Character Name: {state.character_info.get('name')}")
    print(f"   Character Class: {state.character_info.get('class')}")
    print()
    
    # Test 4: Agent Context Retrieval
    print("4. Agent Context Retrieval...")
    agent_context = state.get_agent_context()
    print(f"✅ Agent Context abgerufen:")
    for key, value in agent_context.items():
        if isinstance(value, str) and len(value) > 50:
            print(f"   {key}: {value[:50]}...")
        else:
            print(f"   {key}: {value}")
    print()
    
    # Test 5: Message Handling mit Agent State
    print("5. Message Handling mit Agent State...")
    
    # Simuliere Conversation
    user_msg = ChatMessage(
        type="human",
        content="Ich möchte Option 1 wählen: Schleiche zur Hintertür.",
        session_id=session_id
    )
    state.add_message(user_msg)
    
    ai_msg = ChatMessage(
        type="ai", 
        content="Du schleichst dich erfolgreich zur Hintertür...",
        session_id=session_id
    )
    state.add_message(ai_msg)
    
    print(f"✅ Messages hinzugefügt: {len(state.messages)} total")
    print(f"   Total Messages Counter: {state.total_messages}")
    print(f"   Last User Message: {state.last_user_message[:30]}...")
    print()
    
    # Test 6: SessionInfo with Agent Data
    print("6. SessionInfo with Agent Data...")
    session_info = SessionInfo(
        session_id=state.session_id,
        active=state.active,
        message_count=state.total_messages,
        created_at=state.created_at,
        last_activity=state.last_updated,
        current_agent=state.current_agent,
        has_story_context=bool(state.story_context),
        has_character_info=bool(state.character_info)
    )
    
    print(f"✅ SessionInfo erstellt:")
    print(f"   Session ID: {session_info.session_id}")
    print(f"   Current Agent: {session_info.current_agent}")
    print(f"   Message Count: {session_info.message_count}")
    print(f"   Has Story Context: {session_info.has_story_context}")
    print(f"   Has Character Info: {session_info.has_character_info}")
    print()
    
    # Test 7: State Reset
    print("7. State Reset...")
    print("   Before Reset:")
    print(f"     Agent: {state.current_agent}")
    print(f"     Messages: {len(state.messages)}")
    print(f"     Character Info: {len(state.character_info)} fields")
    
    # Agent State Reset (behält Messages)
    state.reset_agent_state()
    print("   After Agent Reset:")
    print(f"     Agent: {state.current_agent}")
    print(f"     Messages: {len(state.messages)} (should be preserved)")
    print(f"     Character Info: {len(state.character_info)} fields")
    
    # Full Reset 
    state.clear_messages()
    print("   After Full Reset:")
    print(f"     Agent: {state.current_agent}")
    print(f"     Messages: {len(state.messages)}")
    print(f"     Total Messages: {state.total_messages}")
    print()
    
    print("=== Agent State Management Test abgeschlossen ===")


def test_agent_type_validation():
    """Testet die AgentType Validation."""
    
    print("\n=== AgentType Validation Test ===\n")
    
    session_id = str(uuid.uuid4())
    state = ChatState(session_id=session_id)
    
    # Valid Agent Types
    valid_agents = ["story_creator", "gamemaster"]
    
    for agent in valid_agents:
        try:
            state.switch_agent(agent, f"test_{agent}")
            print(f"✅ Valid Agent Type: {agent}")
        except Exception as e:
            print(f"❌ Error with valid agent {agent}: {e}")
    
    print("\n=== AgentType Validation Test abgeschlossen ===")


if __name__ == "__main__":
    test_agent_state_management()
    test_agent_type_validation() 