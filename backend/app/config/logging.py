"""
TextRPG Logging Configuration
Phase 2 Completion - Strukturiertes Logging Setup
"""

import structlog
import logging
import sys
from typing import Dict, Any
from datetime import datetime

def configure_logging(log_level: str = "INFO", enable_debug: bool = False) -> None:
    """
    Configure structured logging for TextRPG.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        enable_debug: Enable debug logging for Phase 2 completion events
    """
    
    # Configure stdlib logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper())
    )
    
    # Configure structlog
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        add_timestamp,
    ]
    
    if enable_debug:
        processors.append(add_phase2_context)
    
    processors.extend([
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ])
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        context_class=dict,
        cache_logger_on_first_use=True,
    )

def add_timestamp(logger, method_name, event_dict):
    """Add timestamp to log entries."""
    event_dict["timestamp"] = datetime.utcnow().isoformat()
    return event_dict

def add_phase2_context(logger, method_name, event_dict):
    """Add Phase 2 specific context to debug logs."""
    
    # Mark Phase 2 events
    if "event_type" in event_dict:
        event_dict["phase2_event"] = True
    
    # Add session context if available
    if "session_id" in event_dict:
        event_dict["session_short"] = event_dict["session_id"][-8:]
    
    return event_dict

# Event Type Classifications for filtering
PHASE2_EVENT_TYPES = {
    "phase_transition": {
        "level": "INFO",
        "description": "Game phase changes (setup → story → gameplay)"
    },
    "agent_switch": {
        "level": "INFO", 
        "description": "Agent transitions (story_creator ↔ gamemaster)"
    },
    "setup_completion": {
        "level": "INFO",
        "description": "Character setup completion detection"
    },
    "message_blocked": {
        "level": "WARNING",
        "description": "Duplicate or invalid messages blocked"
    },
    "action_count": {
        "level": "DEBUG",
        "description": "Action counting events in gameplay phase"
    },
    "transition_trigger": {
        "level": "DEBUG",
        "description": "Transition trigger pattern detection"
    },
    "character_extraction": {
        "level": "DEBUG",
        "description": "Character information extraction from chat"
    },
    "debug_state": {
        "level": "DEBUG", 
        "description": "State snapshots at workflow checkpoints"
    },
    "workflow_error": {
        "level": "ERROR",
        "description": "Errors in workflow execution with recovery info"
    },
    "session_lifecycle": {
        "level": "INFO",
        "description": "Session creation, restoration, cleanup events"
    }
}

def get_log_filter_for_event_types(event_types: list) -> Dict[str, Any]:
    """
    Generate log filter configuration for specific event types.
    
    Args:
        event_types: List of event types to include
        
    Returns:
        Filter configuration dict
    """
    
    return {
        "include_events": event_types,
        "event_metadata": {
            event_type: PHASE2_EVENT_TYPES.get(event_type, {})
            for event_type in event_types
        }
    }

# Predefined filter sets
PRODUCTION_EVENTS = [
    "phase_transition", "agent_switch", "setup_completion",
    "message_blocked", "workflow_error", "session_lifecycle"
]

DEBUG_EVENTS = [
    "action_count", "transition_trigger", "character_extraction", 
    "debug_state"
]

ALL_PHASE2_EVENTS = PRODUCTION_EVENTS + DEBUG_EVENTS

def configure_for_development():
    """Configure logging for development with all Phase 2 events."""
    configure_logging("DEBUG", enable_debug=True)

def configure_for_production():
    """Configure logging for production with essential events only."""
    configure_logging("INFO", enable_debug=False) 