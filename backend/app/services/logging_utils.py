"""
TextRPG Logging Utilities
Phase 2 Completion - Strukturiertes Event Logging
"""

import structlog
from typing import Dict, Any, Optional, Literal
from datetime import datetime

logger = structlog.get_logger()

def log_phase_transition(
    session_id: str,
    from_phase: str,
    to_phase: str,
    trigger: str,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log game phase transitions.
    
    Args:
        session_id: Session identifier
        from_phase: Previous phase
        to_phase: New phase
        trigger: What triggered the transition
        context: Additional context data
    """
    
    logger.info("Game phase transition",
               session_id=session_id,
               from_phase=from_phase,
               to_phase=to_phase,
               trigger=trigger,
               context=context or {},
               event_type="phase_transition")

def log_agent_switch(
    session_id: str,
    from_agent: Optional[str],
    to_agent: str,
    trigger: str,
    phase: str,
    action_count: Optional[int] = None
) -> None:
    """
    Log agent transitions.
    
    Args:
        session_id: Session identifier
        from_agent: Previous agent
        to_agent: New agent
        trigger: What triggered the switch
        phase: Current game phase
        action_count: Current action count (if applicable)
    """
    
    logger.info("Agent transition",
               session_id=session_id,
               from_agent=from_agent,
               to_agent=to_agent,
               trigger=trigger,
               game_phase=phase,
               action_count=action_count,
               event_type="agent_switch")

def log_setup_completion(
    session_id: str,
    trigger_type: str,
    character_info: Optional[Dict[str, Any]] = None,
    detection_method: str = "pattern"
) -> None:
    """
    Log setup phase completion.
    
    Args:
        session_id: Session identifier
        trigger_type: What triggered completion
        character_info: Extracted character information
        detection_method: How completion was detected
    """
    
    logger.info("Setup phase completed",
               session_id=session_id,
               trigger_type=trigger_type,
               character_info=character_info or {},
               detection_method=detection_method,
               event_type="setup_completion")

def log_message_blocked(
    session_id: str,
    block_reason: Literal["duplicate", "too_short", "high_repetition"],
    content_preview: str,
    agent: str,
    additional_info: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log blocked messages with reason.
    
    Args:
        session_id: Session identifier
        block_reason: Why message was blocked
        content_preview: First 50 chars of blocked content
        agent: Which agent generated the blocked message
        additional_info: Additional context
    """
    
    logger.warning("Message blocked",
                  session_id=session_id,
                  block_reason=block_reason,
                  content_preview=content_preview,
                  agent=agent,
                  additional_info=additional_info or {},
                  event_type="message_blocked")

def log_action_count_event(
    session_id: str,
    action_count: int,
    event_type: Literal["increment", "reset", "limit_reached"],
    trigger: Optional[str] = None
) -> None:
    """
    Log action counting events.
    
    Args:
        session_id: Session identifier
        action_count: Current action count
        event_type: Type of action count event
        trigger: What triggered the event
    """
    
    logger.debug("Action count event",
                session_id=session_id,
                action_count=action_count,
                action_event_type=event_type,
                trigger=trigger,
                event_type="action_count")

def log_transition_trigger(
    session_id: str,
    trigger_type: str,
    detected_pattern: Optional[str] = None,
    source: Literal["ai_output", "user_input", "action_limit"] = "ai_output"
) -> None:
    """
    Log transition trigger detection.
    
    Args:
        session_id: Session identifier
        trigger_type: Type of trigger detected
        detected_pattern: Specific pattern that was matched
        source: Where the trigger was detected
    """
    
    logger.debug("Transition trigger detected",
                session_id=session_id,
                trigger_type=trigger_type,
                detected_pattern=detected_pattern,
                source=source,
                event_type="transition_trigger")

def log_character_extraction(
    session_id: str,
    extracted_info: Dict[str, Any],
    extraction_method: str,
    confidence: Optional[str] = None
) -> None:
    """
    Log character information extraction.
    
    Args:
        session_id: Session identifier
        extracted_info: Information that was extracted
        extraction_method: How the info was extracted
        confidence: Confidence level of extraction
    """
    
    logger.debug("Character info extracted",
                session_id=session_id,
                extracted_fields=list(extracted_info.keys()),
                extraction_method=extraction_method,
                confidence=confidence,
                event_type="character_extraction")

def log_workflow_error(
    session_id: str,
    error_type: str,
    error_message: str,
    agent: Optional[str] = None,
    recovery_action: Optional[str] = None
) -> None:
    """
    Log workflow errors with recovery context.
    
    Args:
        session_id: Session identifier
        error_type: Type of error
        error_message: Error description
        agent: Agent where error occurred
        recovery_action: What recovery was attempted
    """
    
    logger.error("Workflow error",
                session_id=session_id,
                error_type=error_type,
                error_message=error_message,
                agent=agent,
                recovery_action=recovery_action,
                event_type="workflow_error")

def log_session_event(
    session_id: str,
    event_type: Literal["created", "restored", "reset", "cleanup"],
    additional_info: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log session lifecycle events.
    
    Args:
        session_id: Session identifier
        event_type: Type of session event
        additional_info: Additional context
    """
    
    logger.info("Session event",
               session_id=session_id,
               session_event_type=event_type,
               additional_info=additional_info or {},
               event_type="session_lifecycle")

def log_debug_state(
    session_id: str,
    state_snapshot: Dict[str, Any],
    checkpoint: str
) -> None:
    """
    Log detailed state for debugging.
    
    Args:
        session_id: Session identifier
        state_snapshot: Current state information
        checkpoint: Where in the flow this snapshot was taken
    """
    
    logger.debug("State snapshot",
                session_id=session_id,
                checkpoint=checkpoint,
                game_phase=state_snapshot.get("game_phase"),
                current_agent=state_snapshot.get("current_agent"),
                setup_complete=state_snapshot.get("setup_complete"),
                action_count=state_snapshot.get("action_count"),
                message_count=state_snapshot.get("total_messages"),
                event_type="debug_state") 