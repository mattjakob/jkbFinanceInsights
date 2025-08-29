"""
/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │             MODELS                  │
 *  └─────────────────────────────────────┘
 *  Core data models for JKB Finance Insights
 * 
 *  Defines data structures used throughout the application,
 *  providing type safety and clear interfaces between components.
 * 
 *  Parameters:
 *  - None
 * 
 *  Returns:
 *  - Data model classes
 * 
 *  Notes:
 *  - Uses dataclasses for immutability and clarity
 *  - Provides validation and conversion methods
 */
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum


class FeedType(str, Enum):
    """
     ┌─────────────────────────────────────┐
     │            FEEDTYPE                 │
     └─────────────────────────────────────┘
     Enumeration of supported feed types
     
     Ensures consistency across the application for feed type references.
    """
    TD_NEWS = "TD NEWS"
    TD_IDEAS_RECENT = "TD IDEAS RECENT"
    TD_IDEAS_POPULAR = "TD IDEAS POPULAR"
    TD_OPINIONS = "TD OPINIONS"


class AIAnalysisStatus(str, Enum):
    """
     ┌─────────────────────────────────────┐
     │        AIANALYSISSTATUS             │
     └─────────────────────────────────────┘
     Status of AI analysis for an insight
     
     Tracks the lifecycle of AI processing.
    """
    EMPTY = "empty"        # No task has operated on the insight yet
    PENDING = "pending"     # Task is queued for processing
    PROCESSING = "processing"  # Task is currently running
    COMPLETED = "completed"    # Task completed successfully
    FAILED = "failed"       # Task failed


class AIAction(str, Enum):
    """
     ┌─────────────────────────────────────┐
     │            AIACTION                 │
     └─────────────────────────────────────┘
     AI-recommended trading actions
     
     Standard set of actions for AI recommendations.
    """
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    WATCH = "WATCH"


@dataclass
class InsightModel:
    """
     ┌─────────────────────────────────────┐
     │         INSIGHTMODEL                │
     └─────────────────────────────────────┘
     Core insight data model
     
     Represents a financial insight with all associated data,
     including AI analysis results.
     
     Parameters:
     - Core fields required for all insights
     - Optional AI analysis fields
     
     Returns:
     - InsightModel instance
     
     Notes:
     - id is None for new insights
     - timestamps use ISO format
    """
    # Core fields
    type: FeedType
    title: str
    content: str
    symbol: str
    exchange: str
    
    # Timestamps
    time_fetched: datetime
    time_posted: datetime
    
    # Optional fields
    id: Optional[int] = None
    image_url: Optional[str] = None
    
    # AI Analysis fields
    ai_image_summary: Optional[str] = None
    ai_summary: Optional[str] = None
    ai_action: Optional[AIAction] = None
    ai_confidence: Optional[float] = None
    ai_event_time: Optional[str] = None
    ai_levels: Optional[str] = None
    ai_analysis_status: AIAnalysisStatus = AIAnalysisStatus.EMPTY
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database operations"""
        return {
            'id': self.id,
            'type': self.type.value,
            'title': self.title,
            'content': self.content,
            'symbol': self.symbol,
            'exchange': self.exchange,
            'timeFetched': self.time_fetched.isoformat(),
            'timePosted': self.time_posted.isoformat(),
            'imageURL': self.image_url,
            'AIImageSummary': self.ai_image_summary,
            'AISummary': self.ai_summary,
            'AIAction': self.ai_action.value if self.ai_action else None,
            'AIConfidence': self.ai_confidence,
            'AIEventTime': self.ai_event_time,
            'AILevels': self.ai_levels,
            'AIAnalysisStatus': self.ai_analysis_status.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InsightModel':
        """Create from dictionary (e.g., database row)"""
        return cls(
            id=data.get('id'),
            type=FeedType(data['type']),
            title=data['title'],
            content=data['content'],
            symbol=data['symbol'],
            exchange=data['exchange'],
            time_fetched=datetime.fromisoformat(data['timeFetched']),
            time_posted=datetime.fromisoformat(data['timePosted']),
            image_url=data.get('imageURL'),
            ai_image_summary=data.get('AIImageSummary'),
            ai_summary=data.get('AISummary'),
            ai_action=AIAction(data['AIAction']) if data.get('AIAction') else None,
            ai_confidence=data.get('AIConfidence'),
            ai_event_time=data.get('AIEventTime'),
            ai_levels=data.get('AILevels'),
            ai_analysis_status=AIAnalysisStatus(data.get('AIAnalysisStatus', 'empty'))
        )


@dataclass
class ScrapedItem:
    """
     ┌─────────────────────────────────────┐
     │         SCRAPEDITEM                 │
     └─────────────────────────────────────┘
     Raw scraped data from external sources
     
     Intermediate format used by scrapers before conversion
     to InsightModel for database storage.
     
     Parameters:
     - Basic fields from scraped content
     - Optional metadata for scraper-specific data
     
     Returns:
     - ScrapedItem instance
     
     Notes:
     - Used only within scraper modules
     - Converted to InsightModel before storage
    """
    title: str
    content: str
    timestamp: datetime
    symbol: str
    exchange: str
    source_url: Optional[str] = None
    image_url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_insight_model(self, feed_type: FeedType) -> InsightModel:
        """Convert to InsightModel for database storage"""
        return InsightModel(
            type=feed_type,
            title=self.title[:200],  # Ensure title fits database constraint
            content=self.content,
            symbol=self.symbol.upper(),
            exchange=self.exchange.upper(),
            time_fetched=datetime.now(),
            time_posted=self.timestamp,
            image_url=self.image_url
        )


@dataclass
class AIAnalysisResult:
    """
     ┌─────────────────────────────────────┐
     │       AIANALYSISRESULT              │
     └─────────────────────────────────────┘
     Result of AI analysis operations
     
     Structured output from AI providers containing
     all analysis components.
     
     Parameters:
     - Analysis results from AI
     
     Returns:
     - AIAnalysisResult instance
     
     Notes:
     - Used by AI providers to return structured data
    """
    summary: str
    action: AIAction
    confidence: float  # 0.0 to 1.0
    event_time: Optional[str] = None
    levels: Optional[Dict[str, Any]] = None
    
    def format_levels(self) -> Optional[str]:
        """Format levels dictionary as string for storage"""
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


@dataclass
class ReportModel:
    """
     ┌─────────────────────────────────────┐
     │         REPORTMODEL                 │
     └─────────────────────────────────────┘
     AI analysis report data model
     
     Represents a standalone AI analysis report for a symbol,
     independent of specific insights.
     
     Parameters:
     - Core fields for report tracking
     - AI analysis results
     
     Returns:
     - ReportModel instance
     
     Notes:
     - Used for storing consolidated AI analysis
     - Can aggregate multiple insights for a symbol
    """
    # Core fields
    time_fetched: datetime
    symbol: str
    
    # AI Analysis fields
    ai_summary: str
    ai_action: AIAction
    ai_confidence: float
    ai_event_time: Optional[str] = None
    ai_levels: Optional[str] = None
    ai_analysis_status: AIAnalysisStatus = AIAnalysisStatus.COMPLETED
    
    # Optional fields
    id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database operations"""
        return {
            'id': self.id,
            'timeFetched': self.time_fetched.isoformat(),
            'symbol': self.symbol,
            'AISummary': self.ai_summary,
            'AIAction': self.ai_action.value,
            'AIConfidence': self.ai_confidence,
            'AIEventTime': self.ai_event_time,
            'AILevels': self.ai_levels,
            'AIAnalysisStatus': self.ai_analysis_status.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReportModel':
        """Create from dictionary (e.g., database row)"""
        return cls(
            id=data.get('id'),
            time_fetched=datetime.fromisoformat(data['timeFetched']),
            symbol=data['symbol'],
            ai_summary=data['AISummary'],
            ai_action=AIAction(data['AIAction']),
            ai_confidence=data['AIConfidence'],
            ai_event_time=data.get('AIEventTime'),
            ai_levels=data.get('AILevels'),
            ai_analysis_status=AIAnalysisStatus(data.get('AIAnalysisStatus', 'completed'))
        )



