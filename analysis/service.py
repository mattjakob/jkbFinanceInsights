"""
/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │       ANALYSIS SERVICE              │
 *  └─────────────────────────────────────┘
 *  Main service for AI analysis
 * 
 *  Provides a high-level interface for AI analysis,
 *  abstracting away the specific provider implementation.
 * 
 *  Parameters:
 *  - provider: AIProvider implementation
 * 
 *  Returns:
 *  - AnalysisService instance
 * 
 *  Notes:
 *  - Provider can be swapped at runtime
 *  - Handles both text and image analysis
 */
"""

from typing import Dict, Any, Optional

from .providers.base import AIProvider
from .models import AnalysisRequest, ImageAnalysisRequest, AnalysisResult
from debugger import debug_info, debug_error


class AnalysisService:
    """
     ┌─────────────────────────────────────┐
     │       ANALYSISSERVICE               │
     └─────────────────────────────────────┘
     High-level service for AI analysis
     
     Coordinates AI analysis operations using the
     configured provider.
    """
    
    def __init__(self, provider: Optional[AIProvider] = None):
        if provider is None:
            # Default to OpenAI provider
            from .providers.openai import OpenAIProvider
            provider = OpenAIProvider()
        
        self.provider = provider
    
    def analyze_text(self, 
                    text: str,
                    context: Dict[str, Any]) -> AnalysisResult:
        """
         ┌─────────────────────────────────────┐
         │        ANALYZE_TEXT                 │
         └─────────────────────────────────────┘
         Analyze text content
         
         Parameters:
         - text: Content to analyze
         - context: Additional context (symbol, type, etc.)
         
         Returns:
         - AnalysisResult with structured output
        """
        request = AnalysisRequest(text=text, context=context)
        
        debug_info(f"Analyzing text for {request.symbol}")
        
        try:
            result = self.provider.analyze_text(request)
            debug_info(f"Text analysis completed for {request.symbol}")
            return result
            
        except Exception as e:
            debug_error(f"Text analysis failed: {e}")
            raise
    
    def analyze_image(self,
                     image_url: str,
                     context: Dict[str, Any]) -> str:
        """
         ┌─────────────────────────────────────┐
         │       ANALYZE_IMAGE                 │
         └─────────────────────────────────────┘
         Analyze image content
         
         Parameters:
         - image_url: URL of image to analyze
         - context: Additional context (symbol, etc.)
         
         Returns:
         - String description of analysis
        """
        request = ImageAnalysisRequest(image_url=image_url, context=context)
        
        debug_info(f"Analyzing image for {request.symbol}")
        
        try:
            result = self.provider.analyze_image(request)
            debug_info(f"Image analysis completed for {request.symbol}")
            return result
            
        except Exception as e:
            debug_error(f"Image analysis failed: {e}")
            raise
    
    async def analyze_text_async(self,
                                text: str,
                                context: Dict[str, Any]) -> AnalysisResult:
        """Async version of analyze_text"""
        request = AnalysisRequest(text=text, context=context)
        
        insight_id = context.get('insight_id', 'unknown')
        debug_info(f"OpenAI Text Analysis on #{insight_id}")
        
        try:
            result = await self.provider.analyze_text_async(request)
            debug_info(f"Text analysis completed for {request.symbol}")
            return result
            
        except Exception as e:
            debug_error(f"Text analysis failed: {e}")
            raise
    
    async def analyze_image_async(self,
                                 image_url: str,
                                 context: Dict[str, Any]) -> str:
        """Async version of analyze_image"""
        request = ImageAnalysisRequest(image_url=image_url, context=context)
        
        insight_id = context.get('insight_id', 'unknown')
        debug_info(f"OpenAI Image Analysis on ID{insight_id}")
        
        try:
            result = await self.provider.analyze_image_async(request)
            debug_info(f"Image analysis completed for {request.symbol}")
            return result
            
        except Exception as e:
            debug_error(f"Image analysis failed: {e}")
            raise
    
    def analyze_report(self,
                      symbol: str,
                      content: str) -> AnalysisResult:
        """
         ┌─────────────────────────────────────┐
         │        ANALYZE_REPORT               │
         └─────────────────────────────────────┘
         Generate AI report analysis (synchronous)
         
         Parameters:
         - symbol: Trading symbol to analyze
         - content: Content to analyze
         
         Returns:
         - AnalysisResult with structured output
        """
        request = AnalysisRequest(
            text=content,
            context={
                'symbol': symbol
            }
        )
        
        debug_info(f"OpenAI Report Analysis for {symbol}")
        
        try:
            result = self.provider.analyze_report(request)
            debug_info(f"Report analysis completed for {symbol}")
            return result
            
        except Exception as e:
            debug_error(f"Report analysis failed: {e}")
            raise

    async def analyze_report_async(self,
                                  symbol: str,
                                  content: str) -> AnalysisResult:
        """Generate AI report analysis"""
        request = AnalysisRequest(
            text=content,
            context={
                'symbol': symbol
            }
        )
        
        debug_info(f"OpenAI Report Analysis for {symbol}")
        
        try:
            result = await self.provider.analyze_report_async(request)
            debug_info(f"Report analysis completed for {symbol}")
            return result
            
        except Exception as e:
            debug_error(f"Report analysis failed: {e}")
            raise
    
    def set_provider(self, provider: AIProvider):
        """
         ┌─────────────────────────────────────┐
         │        SET_PROVIDER                 │
         └─────────────────────────────────────┘
         Change the AI provider
         
         Allows runtime switching of AI providers.
         
         Parameters:
         - provider: New AIProvider implementation
        """
        self.provider = provider
        debug_info(f"Analysis provider changed to {provider.__class__.__name__}")



