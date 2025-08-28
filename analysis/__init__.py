"""
AI Analysis module for JKB Finance Insights

This module provides AI-powered analysis functionality
with pluggable providers for easy extensibility.
"""

from .service import AnalysisService
from .models import AnalysisRequest, ImageAnalysisRequest, AnalysisResult, AnalysisAction
from .providers.base import AIProvider
from .providers.openai import OpenAIProvider

__all__ = [
    # Service
    'AnalysisService',
    # Models
    'AnalysisRequest',
    'ImageAnalysisRequest',
    'AnalysisResult',
    'AnalysisAction',
    # Providers
    'AIProvider',
    'OpenAIProvider'
]



