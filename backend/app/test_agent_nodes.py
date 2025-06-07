"""
Test-Skript für die Agent-Nodes.
Testet die Agent-Node Integration mit State Management.
"""

import asyncio
import uuid
from app.models import ChatState, create_human_message
from app.graph.nodes_agents import story_creator_node, gamemaster_node, determine_next_agent
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_agent_nodes():
    """Testet die Agent-Nodes mit State Management."""
    
    print("=== Agent Nodes Test ===\n")
    
    # Test 1: Story Creator Node
    print("1. Teste Story Creator Node...")
    
    session_id = str(uuid.uuid4())
    state = ChatState(session_id=session_id)
    
    # Simulate user message
    state.last_user_message = "Erstelle ein Fantasy-Abenteuer mit einem Dieb"
    state.processing = True
    
    try:
        result = await story_creator_node(state)
        
        print(f"✅ Story Creator Node erfolgreich ausgeführt")
        print(f"   Returned Keys: {list(result.keys())}")
        print(f"   Processing: {result.get('processing')}")
        print(f"   Messages: {len(result.get('messages', []))}")
        print(f"   Current Agent: {result.get('current_agent')}")
        print(f"   Story Context: {result.get('story_context', '')[:100]}...")
        
        # Check for transition
        if result.get('transition_trigger'):
            print(f"   Transition Trigger: {result['transition_trigger']}")
        
        # Update state with result
        for key, value in result.items():
            if hasattr(state, key):
                setattr(state, key, value)
                
        print(f"   Last AI Message: {state.messages[-1].content[:100] if state.messages else 'None'}...")
        
    except Exception as e:
        print(f"❌ Fehler beim Testen des Story Creator Nodes: {e}")
        
    print("-" * 50)
    
    # Test 2: Agent Transition Logic
    print("\n2. Teste Agent Transition Logic...")
    
    # Test different scenarios
    scenarios = [
        {"agent": None, "trigger": None, "processing": True, "message": "Test"},
        {"agent": "story_creator", "trigger": "handlungsoptionen_präsentiert", "processing": True, "message": "Option 1"},
        {"agent": "gamemaster", "trigger": "neues_kapitel_benötigt", "processing": True, "message": "Weiter"},
        {"agent": "story_creator", "trigger": None, "processing": False, "message": None}
    ]
    
    for i, scenario in enumerate(scenarios):
        test_state = ChatState(session_id=str(uuid.uuid4()))
        test_state.current_agent = scenario["agent"]
        test_state.transition_trigger = scenario["trigger"] 
        test_state.processing = scenario["processing"]
        test_state.last_user_message = scenario["message"]
        
        next_agent = determine_next_agent(test_state)
        
        print(f"   Scenario {i+1}:")
        print(f"     Current: {scenario['agent']} | Trigger: {scenario['trigger']}")
        print(f"     Processing: {scenario['processing']} | Message: {bool(scenario['message'])}")
        print(f"     → Next Agent: {next_agent}")
    
    print("-" * 50)
    
    # Test 3: Gamemaster Node (falls Story Creator erfolgreich war)
    print("\n3. Teste Gamemaster Node...")
    
    if state.transition_trigger == "handlungsoptionen_präsentiert":
        # Simulate user choosing an option
        state.last_user_message = "Ich wähle Option 1: Schleiche zur Hintertür"
        state.processing = True
        
        try:
            result = await gamemaster_node(state)
            
            print(f"✅ Gamemaster Node erfolgreich ausgeführt")
            print(f"   Returned Keys: {list(result.keys())}")
            print(f"   Processing: {result.get('processing')}")
            print(f"   Messages: {len(result.get('messages', []))}")
            print(f"   Current Agent: {result.get('current_agent')}")
            print(f"   Character Info: {result.get('character_info', {})}")
            
            # Check for transition back
            if result.get('transition_trigger'):
                print(f"   Transition Trigger: {result['transition_trigger']}")
            
            # Update state
            for key, value in result.items():
                if hasattr(state, key):
                    setattr(state, key, value)
                    
            print(f"   Last AI Message: {state.messages[-1].content[:100] if state.messages else 'None'}...")
            
        except Exception as e:
            print(f"❌ Fehler beim Testen des Gamemaster Nodes: {e}")
    else:
        print("   Übersprungen - kein Transition Trigger vom Story Creator")
    
    print("-" * 50)
    
    # Test 4: Full Agent Context
    print("\n4. Teste Full Agent Context...")
    
    agent_context = state.get_agent_context()
    print(f"✅ Agent Context abgerufen:")
    for key, value in agent_context.items():
        if isinstance(value, str) and len(value) > 50:
            print(f"   {key}: {value[:50]}...")
        else:
            print(f"   {key}: {value}")
    
    print(f"\n   Session Message Count: {len(state.messages)}")
    print(f"   Session Total Messages: {state.total_messages}")
    
    print("\n=== Agent Nodes Test abgeschlossen ===")


async def test_error_handling():
    """Testet Error Handling in den Agent-Nodes."""
    
    print("\n=== Error Handling Test ===\n")
    
    # Test mit ungültigem State
    print("1. Teste ungültigen State...")
    
    session_id = str(uuid.uuid4())
    state = ChatState(session_id=session_id)
    # Kein last_user_message gesetzt
    
    try:
        result = await story_creator_node(state)
        
        if result.get("processing") == False:
            print("✅ Graceful handling bei fehlendem User Message")
        else:
            print("❌ Unerwartetes Verhalten bei fehlendem User Message")
            
    except Exception as e:
        print(f"❌ Exception bei fehlendem User Message: {e}")
    
    print("\n=== Error Handling Test abgeschlossen ===")


if __name__ == "__main__":
    asyncio.run(test_agent_nodes())
    asyncio.run(test_error_handling()) 