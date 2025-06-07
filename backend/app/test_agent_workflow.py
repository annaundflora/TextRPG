"""
Test-Skript für den Agent-basierten Workflow.
Testet den kompletten LangGraph Agent-Flow von Start bis Ende.
"""

import asyncio
import uuid
from app.models import ChatState
from app.graph import create_agent_workflow, get_phase2_workflow, reset_workflow_cache, determine_initial_agent
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_workflow_creation():
    """Testet die Workflow-Erstellung und Compilation."""
    
    print("=== Workflow Creation Test ===\n")
    
    # Test 1: Create Agent Workflow
    print("1. Teste Agent Workflow Creation...")
    
    try:
        workflow = create_agent_workflow()
        print(f"✅ Agent Workflow erfolgreich erstellt")
        print(f"   Workflow Typ: {type(workflow)}")
        
        # Check nodes
        nodes = workflow.nodes if hasattr(workflow, 'nodes') else "N/A"
        print(f"   Nodes: {nodes}")
        
    except Exception as e:
        print(f"❌ Fehler beim Erstellen des Agent Workflows: {e}")
        return False
    
    print("-" * 50)
    
    # Test 2: Compile Workflow
    print("\n2. Teste Workflow Compilation...")
    
    try:
        # Reset cache first
        reset_workflow_cache()
        
        compiled_workflow = get_phase2_workflow()
        print(f"✅ Phase 2 Workflow erfolgreich kompiliert")
        print(f"   Compiled Workflow Typ: {type(compiled_workflow)}")
        
    except Exception as e:
        print(f"❌ Fehler beim Kompilieren des Workflows: {e}")
        return False
    
    print("-" * 50)
    
    # Test 3: Initial Agent Determination
    print("\n3. Teste Initial Agent Determination...")
    
    scenarios = [
        {"agent": None, "active": True, "expected": "story_creator"},
        {"agent": "story_creator", "active": True, "expected": "story_creator"},
        {"agent": "gamemaster", "active": True, "expected": "gamemaster"},
        {"agent": None, "active": False, "expected": "end"}
    ]
    
    for i, scenario in enumerate(scenarios):
        test_state = ChatState(session_id=str(uuid.uuid4()))
        test_state.current_agent = scenario["agent"]
        test_state.active = scenario["active"]
        
        result = determine_initial_agent(test_state)
        
        success = result == scenario["expected"]
        status = "✅" if success else "❌"
        
        print(f"   Scenario {i+1}: {status}")
        print(f"     Agent: {scenario['agent']} | Active: {scenario['active']}")
        print(f"     Expected: {scenario['expected']} | Got: {result}")
        
    print("\n=== Workflow Creation Test abgeschlossen ===")
    return True


async def test_full_workflow_execution():
    """Testet die komplette Workflow-Ausführung."""
    
    print("\n=== Full Workflow Execution Test ===\n")
    
    # Test 1: Complete Agent Flow
    print("1. Teste kompletten Agent-Flow...")
    
    try:
        # Get compiled workflow
        workflow = get_phase2_workflow()
        
        # Create initial state
        session_id = str(uuid.uuid4())
        initial_state = ChatState(session_id=session_id)
        initial_state.last_user_message = "Erstelle ein Cyberpunk-Abenteuer"
        initial_state.processing = True
        
        print(f"   Session ID: {session_id}")
        print(f"   Initial User Message: {initial_state.last_user_message}")
        
        # Execute workflow
        print("\n   Starte Workflow-Ausführung...")
        result = await workflow.ainvoke(initial_state)
        
        print(f"✅ Workflow erfolgreich ausgeführt")
        print(f"   Final State Keys: {list(result.keys()) if isinstance(result, dict) else 'State Object'}")
        
        # Check result state
        if hasattr(result, 'messages'):
            print(f"   Messages: {len(result.messages)}")
            if result.messages:
                last_message = result.messages[-1]
                print(f"   Last Message: {last_message.content[:100]}...")
                print(f"   Last Message Type: {last_message.type}")
        
        if hasattr(result, 'current_agent'):
            print(f"   Current Agent: {result.current_agent}")
            
        if hasattr(result, 'transition_trigger'):
            print(f"   Transition Trigger: {result.transition_trigger}")
            
        if hasattr(result, 'story_context'):
            context = result.story_context
            if context:
                print(f"   Story Context: {context[:100]}...")
        
    except Exception as e:
        print(f"❌ Fehler beim Ausführen des Workflows: {e}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        return False
    
    print("-" * 50)
    
    # Test 2: Multi-Turn Conversation
    print("\n2. Teste Multi-Turn Conversation...")
    
    try:
        # Continue with the session if possible
        if hasattr(result, 'session_id'):
            # Simulate user response to action options
            if hasattr(result, 'transition_trigger') and result.transition_trigger == "handlungsoptionen_präsentiert":
                print("   Agent hat Handlungsoptionen präsentiert - simuliere User Choice...")
                
                # Create follow-up state
                followup_state = result
                followup_state.last_user_message = "Ich wähle Option A"
                followup_state.processing = True
                
                # Execute again
                followup_result = await workflow.ainvoke(followup_state)
                
                print(f"✅ Follow-up Workflow erfolgreich ausgeführt")
                print(f"   Follow-up Messages: {len(followup_result.messages) if hasattr(followup_result, 'messages') else 'N/A'}")
                print(f"   Follow-up Agent: {followup_result.current_agent if hasattr(followup_result, 'current_agent') else 'N/A'}")
                
                if hasattr(followup_result, 'messages') and followup_result.messages:
                    last_msg = followup_result.messages[-1]
                    print(f"   Follow-up Response: {last_msg.content[:100]}...")
            else:
                print("   Kein Agent-Switch detektiert - überspringe Follow-up Test")
        else:
            print("   Keine Session ID verfügbar - überspringe Follow-up Test")
            
    except Exception as e:
        print(f"❌ Fehler beim Follow-up Test: {e}")
    
    print("\n=== Full Workflow Execution Test abgeschlossen ===")
    return True


async def test_workflow_error_handling():
    """Testet Error Handling im Workflow."""
    
    print("\n=== Workflow Error Handling Test ===\n")
    
    # Test 1: Invalid State
    print("1. Teste ungültigen State...")
    
    try:
        workflow = get_phase2_workflow()
        
        # Create invalid state (no session_id)
        invalid_state = ChatState(session_id="")
        invalid_state.active = False
        
        result = await workflow.ainvoke(invalid_state)
        
        print(f"✅ Workflow handled invalid state gracefully")
        print(f"   Result: {type(result)}")
        
    except Exception as e:
        print(f"❌ Workflow failed on invalid state: {e}")
    
    print("-" * 50)
    
    # Test 2: Empty User Message
    print("\n2. Teste leere User Message...")
    
    try:
        workflow = get_phase2_workflow()
        
        empty_state = ChatState(session_id=str(uuid.uuid4()))
        empty_state.last_user_message = ""
        empty_state.processing = True
        
        result = await workflow.ainvoke(empty_state)
        
        print(f"✅ Workflow handled empty message gracefully")
        
    except Exception as e:
        print(f"❌ Workflow failed on empty message: {e}")
    
    print("\n=== Workflow Error Handling Test abgeschlossen ===")


if __name__ == "__main__":
    asyncio.run(test_workflow_creation())
    asyncio.run(test_full_workflow_execution())
    asyncio.run(test_workflow_error_handling()) 