"""
/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │       ANALYSIS MODELS               │
 *  └─────────────────────────────────────┘
 *  Data models for AI analysis module
 * 
 *  Defines the data structures used for AI analysis
 *  requests and responses.
 * 
 *  Parameters:
 *  - None
 * 
 *  Returns:
 *  - Analysis data models
 * 
 *  Notes:
 *  - Independent of core models
 *  - Used only within analysis module
 */
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from enum import Enum


# Import from core to maintain consistency
from core.models import TradingAction

# Alias for analysis module
AnalysisAction = TradingAction


@dataclass
class AnalysisRequest:
    """
     ┌─────────────────────────────────────┐
     │       ANALYSISREQUEST               │
     └─────────────────────────────────────┘
     Request for AI analysis
     
     Contains all data needed for analysis.
    """
    text: str
    context: Dict[str, Any]
    
    @property
    def symbol(self) -> str:
        """Get symbol from context"""
        return self.context.get('symbol', '')
    
    @property
    def item_type(self) -> str:
        """Get item type from context"""
        return self.context.get('type', '')
    
    @property
    def title(self) -> str:
        """Get title from context"""
        return self.context.get('title', '')
    
    @property
    def technical(self) -> str:
        """Get technical analysis from context"""
        return self.context.get('technical', '')


@dataclass
class ImageAnalysisRequest:
    """
     ┌─────────────────────────────────────┐
     │     IMAGEANALYSISREQUEST            │
     └─────────────────────────────────────┘
     Request for image analysis
     
     Contains image URL and context for analysis.
    """
    image_url: str
    context: Dict[str, Any]
    
    @property
    def symbol(self) -> str:
        """Get symbol from context"""
        return self.context.get('symbol', '')


@dataclass
class AnalysisResult:
    """
     ┌─────────────────────────────────────┐
     │        ANALYSISRESULT               │
     └─────────────────────────────────────┘
     Result of AI analysis
     
     Structured output containing all analysis components.
    """
    summary: str
    action: AnalysisAction
    confidence: float  # 0.0 to 1.0
    event_time: Optional[str] = None
    levels: Optional[Dict[str, Any]] = None
    
    def format_levels(self) -> Optional[str]:
        """Format levels for storage"""
        if not self.levels:
            return None
        
        parts = []
        if self.levels.get('entry'):
            parts.append(f"E: {self.levels['entry']}")
        if self.levels.get('take_profit'):
            parts.append(f"TP: {self.levels['take_profit']}")
        if self.levels.get('stop_loss'):
            parts.append(f"SL: {self.levels['stop_loss']}")
        if self.levels.get('support'):
            support = self.levels['support']
            if isinstance(support, list):
                parts.append(f"S: {', '.join(map(str, support))}")
            else:
                parts.append(f"S: {support}")
        if self.levels.get('resistance'):
            parts.append(f"R: {self.levels['resistance']}")
        
        return " | ".join(parts) if parts else None



