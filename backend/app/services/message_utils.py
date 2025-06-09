"""
TextRPG Message Utilities
Phase 2 Completion - Message Deduplication & Processing
"""

import hashlib
import structlog
from typing import Optional

from ..models import ChatState

logger = structlog.get_logger()

def generate_message_hash(content: str) -> str:
    """
    Generate hash for message content.
    
    Args:
        content: Message content to hash
        
    Returns:
        8-character hash string
    """
    return hashlib.md5(content.encode('utf-8')).hexdigest()[:8]

def is_duplicate_response(state: ChatState, new_content: str) -> bool:
    """
    Check if response is duplicate of last AI message.
    
    Args:
        state: Current ChatState
        new_content: New message content to check
        
    Returns:
        True if content is duplicate
    """
    if not state.last_message_hash:
        return False
    
    new_hash = generate_message_hash(new_content)
    is_duplicate = new_hash == state.last_message_hash
    
    if is_duplicate:
        logger.warning("Duplicate message detected",
                      session_id=state.session_id,
                      hash=new_hash,
                      content_preview=new_content[:50] + "...")
    
    return is_duplicate

def deduplicate_message(state: ChatState, content: str) -> Optional[str]:
    """
    Return content only if not duplicate, else None.
    
    Args:
        state: Current ChatState
        content: Message content to check
        
    Returns:
        Content if not duplicate, None if duplicate
    """
    if is_duplicate_response(state, content):
        logger.warning("Message blocked due to duplication",
                      session_id=state.session_id,
                      hash=generate_message_hash(content))
        return None
    
    return content

def update_message_hash(state: ChatState, content: str) -> None:
    """
    Update the message hash in state after successful message.
    
    Args:
        state: ChatState to update
        content: Content of the new message
    """
    state.set_message_hash(content)
    
    logger.debug("Message hash updated",
                session_id=state.session_id,
                hash=state.last_message_hash,
                content_length=len(content))

def should_block_message(state: ChatState, content: str) -> bool:
    """
    Determine if a message should be blocked (comprehensive check).
    
    Args:
        state: Current ChatState
        content: Message content to evaluate
        
    Returns:
        True if message should be blocked
    """
    
    # Check for empty or too short content
    if not content or len(content.strip()) < 10:
        logger.warning("Message blocked: Too short",
                      session_id=state.session_id,
                      content_length=len(content.strip()) if content else 0)
        return True
    
    # Check for duplication
    if is_duplicate_response(state, content):
        return True
    
    # Check for obvious repetition patterns (same words repeated)
    words = content.lower().split()
    if len(words) > 4:
        unique_words = set(words)
        repetition_ratio = len(unique_words) / len(words)
        if repetition_ratio < 0.3:  # More than 70% repeated words
            logger.warning("Message blocked: High repetition ratio",
                          session_id=state.session_id,
                          repetition_ratio=repetition_ratio)
            return True
    
    return False

def clean_message_content(content: str) -> str:
    """
    Clean and normalize message content.
    
    Args:
        content: Raw message content
        
    Returns:
        Cleaned message content
    """
    
    # Basic cleanup
    cleaned = content.strip()
    
    # Remove excessive whitespace
    import re
    cleaned = re.sub(r'\s+', ' ', cleaned)
    
    # Remove duplicate punctuation
    cleaned = re.sub(r'([.!?]){2,}', r'\1', cleaned)
    
    return cleaned 