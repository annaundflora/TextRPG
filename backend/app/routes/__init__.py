"""
TextRPG Routes Package
Exportiert alle FastAPI Router
"""

from .chat import router as chat_router

__all__ = ["chat_router"] 