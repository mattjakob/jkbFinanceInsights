"""
Views module for JKB Finance Insights

This module contains web route handlers that render HTML templates
for the user interface.
"""

from .web_routes import router as web_router

__all__ = ['web_router']
