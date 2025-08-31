"""
/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │    INSIGHT ANALYSIS SERVICE         │
 *  └─────────────────────────────────────┘
 *  Business logic for AI analysis of insights
 * 
 *  Handles AI-powered analysis of insight content including
 *  text analysis, image analysis, and generating trading
 *  recommendations.
 * 
 *  Parameters:
 *  - core_service: Core AnalysisService from analysis module
 * 
 *  Returns:
 *  - InsightAnalysisService instance
 * 
 *  Notes:
 *  - Focuses on analyzing individual insights
 *  - Provides structured AI analysis results
 *  - Does NOT handle report generation
 */
"""

from typing import Dict, Any, Optional
from analysis.service import AnalysisService as CoreAnalysisService
from debugger import debug_info, debug_error


class InsightAnalysisService:
    """
     ┌─────────────────────────────────────┐
     │    INSIGHTANALYSISSERVICE           │
     └─────────────────────────────────────┘
     Service for AI analysis of insights
     
     Provides AI-powered analysis of insight content,
     generating trading recommendations and summaries.
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
