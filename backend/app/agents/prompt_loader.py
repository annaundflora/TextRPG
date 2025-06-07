"""
Prompt Loader Utilities für Agent-Prompts.
Lädt Markdown-Dateien aus backend/prompts/ mit UTF-8 Encoding.
"""

import os
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def load_prompt_from_file(filename: str) -> str:
    """
    Lädt einen Prompt aus einer Markdown-Datei im backend/prompts/ Verzeichnis.
    
    Args:
        filename: Name der Prompt-Datei (z.B. "prompt_story_creator.md")
        
    Returns:
        str: Inhalt der Prompt-Datei
        
    Raises:
        FileNotFoundError: Wenn die Datei nicht existiert
        UnicodeDecodeError: Bei Encoding-Problemen
    """
    try:
        # Pfad zur Prompt-Datei ermitteln
        # Von backend/app/agents/ aus: ../../prompts/
        current_dir = Path(__file__).parent
        prompts_dir = current_dir.parent.parent / "prompts"
        prompt_file_path = prompts_dir / filename
        
        logger.info(f"Lade Prompt aus: {prompt_file_path}")
        
        # Datei mit UTF-8 Encoding lesen
        with open(prompt_file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        if not content.strip():
            logger.warning(f"Prompt-Datei {filename} ist leer")
            return ""
            
        logger.info(f"Prompt erfolgreich geladen: {len(content)} Zeichen")
        return content
        
    except FileNotFoundError:
        logger.error(f"Prompt-Datei nicht gefunden: {prompt_file_path}")
        raise
    except UnicodeDecodeError as e:
        logger.error(f"UTF-8 Decoding-Fehler in {filename}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unerwarteter Fehler beim Laden von {filename}: {e}")
        raise


def extract_system_prompt(markdown_content: str) -> str:
    """
    Extrahiert den System-Prompt aus dem Markdown-Inhalt.
    
    Entfernt Markdown-Header und bereitet den Text für LLM-Usage vor.
    
    Args:
        markdown_content: Vollständiger Markdown-Inhalt
        
    Returns:
        str: Bereinigter System-Prompt
    """
    if not markdown_content.strip():
        return ""
    
    # Entferne erste Zeile wenn sie ein Markdown-Header ist
    lines = markdown_content.split('\n')
    if lines and lines[0].startswith('# '):
        lines = lines[1:]
    
    # Füge zusammen und entferne übermäßige Leerzeilen
    cleaned_content = '\n'.join(lines)
    
    # Reduziere mehrfache Leerzeilen auf maximal zwei
    while '\n\n\n' in cleaned_content:
        cleaned_content = cleaned_content.replace('\n\n\n', '\n\n')
    
    return cleaned_content.strip()


def get_story_creator_prompt() -> str:
    """Lädt und bereitet den Story Creator Prompt vor."""
    try:
        raw_content = load_prompt_from_file("prompt_story_creator.md")
        return extract_system_prompt(raw_content)
    except Exception as e:
        logger.error(f"Fehler beim Laden des Story Creator Prompts: {e}")
        # Fallback zu Placeholder
        return "Du bist ein Story Creator für TextRPG Adventures. Erstelle fesselnde Geschichten."


def get_gamemaster_prompt() -> str:
    """Lädt und bereitet den Gamemaster Prompt vor."""
    try:
        raw_content = load_prompt_from_file("prompt_game_master.md")
        return extract_system_prompt(raw_content)
    except Exception as e:
        logger.error(f"Fehler beim Laden des Gamemaster Prompts: {e}")
        # Fallback zu Placeholder
        return "Du bist ein Gamemaster für TextRPG Adventures. Verarbeite Spieleraktionen und biete Optionen." 