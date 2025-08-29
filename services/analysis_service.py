"""
/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │       ANALYSIS SERVICE              │
 *  └─────────────────────────────────────┘
 *  Business logic for AI analysis operations
 * 
 *  Coordinates AI analysis operations and provides
 *  business logic layer for analysis management.
 * 
 *  Parameters:
 *  - analysis_service: AnalysisService from analysis module
 * 
 *  Returns:
 *  - AnalysisService instance
 * 
 *  Notes:
 *  - Wraps the analysis module's service for business logic
 *  - Handles analysis coordination and validation
 */
"""

from typing import Dict, Any, Optional
from analysis.service import AnalysisService as CoreAnalysisService
from debugger import debug_info, debug_error


class AnalysisService:
    """
     ┌─────────────────────────────────────┐
     │       ANALYSISSERVICE               │
     └─────────────────────────────────────┘
     Business logic service for AI analysis
     
     Provides high-level operations for AI analysis,
     implementing business rules and coordination.
    """
    
    def __init__(self, core_service: Optional[CoreAnalysisService] = None):
        self.core_service = core_service or CoreAnalysisService()
    
    def analyze_insight_text(self, 
                           text: str, 
                           context: Dict[str, Any]) -> Dict[str, Any]:
        """
         ┌─────────────────────────────────────┐
         │      ANALYZE_INSIGHT_TEXT           │
         └─────────────────────────────────────┘
         Analyze insight text content
         
         Parameters:
         - text: Text content to analyze
         - context: Context information (symbol, type, etc.)
         
         Returns:
         - Dictionary with analysis results
        """
        try:
            result = self.core_service.analyze_text(text, context)
            
            return {
                "success": True,
                "summary": result.summary,
                "action": result.action.value,
                "confidence": result.confidence,
                "event_time": result.event_time,
                "levels": result.format_levels()
            }
            
        except Exception as e:
            debug_error(f"Text analysis failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def analyze_insight_image(self, 
                            image_url: str, 
                            context: Dict[str, Any]) -> Dict[str, Any]:
        """
         ┌─────────────────────────────────────┐
         │     ANALYZE_INSIGHT_IMAGE           │
         └─────────────────────────────────────┘
         Analyze insight image content
         
         Parameters:
         - image_url: URL of image to analyze
         - context: Context information (symbol, etc.)
         
         Returns:
         - Dictionary with image analysis results
        """
        try:
            result = self.core_service.analyze_image(image_url, context)
            
            return {
                "success": True,
                "image_summary": result
            }
            
        except Exception as e:
            debug_error(f"Image analysis failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
