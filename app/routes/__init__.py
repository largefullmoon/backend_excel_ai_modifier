"""
Routes package for the Excel AI Modifier application
"""

from .health import router as health_router
from .excel import router as excel_router

__all__ = [
    "health_router",
    "excel_router"
]
