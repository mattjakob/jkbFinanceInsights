"""
/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │         BASE PROVIDER               │
 *  └─────────────────────────────────────┘
 *  Abstract base class for AI providers
 * 
 *  Defines the interface that all AI providers must implement,
 *  allowing for easy switching between different AI services.
 * 
 *  Parameters:
 *  - None
 * 
 *  Returns:
 *  - Abstract provider interface
 * 
 *  Notes:
 *  - All providers must implement analyze_text and analyze_image
 *  - Supports both sync and async methods
 */
"""

from abc import ABC, abstractmethod
from typing import Optional

from ..models import AnalysisRequest, ImageAnalysisRequest, AnalysisResult


class AIProvider(ABC):
    """
     ┌─────────────────────────────────────┐
     │          AIPROVIDER                 │
     └─────────────────────────────────────┘
     Abstract base class for AI providers
     
     Defines the interface for AI analysis providers.
    """
    
    @abstractmethod
    def analyze_text(self, request: AnalysisRequest) -> AnalysisResult:
        """
         ┌─────────────────────────────────────┐
         │        ANALYZE_TEXT                 │
         └─────────────────────────────────────┘
         Analyze text content
         
         Parameters:
         - request: Analysis request with text and context
         
         Returns:
         - AnalysisResult with structured output
        """
        pass
    
    @abstractmethod
    def analyze_image(self, request: ImageAnalysisRequest) -> str:
        """
         ┌─────────────────────────────────────┐
         │       ANALYZE_IMAGE                 │
         └─────────────────────────────────────┘
         Analyze image content
         
         Parameters:
         - request: Image analysis request
         
         Returns:
         - String description of image analysis
        """
        pass
    
    async def analyze_text_async(self, request: AnalysisRequest) -> AnalysisResult:
        """Async wrapper for text analysis"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.analyze_text, request)
    
    async def analyze_image_async(self, request: ImageAnalysisRequest) -> str:
        """Async wrapper for image analysis"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.analyze_image, request)



