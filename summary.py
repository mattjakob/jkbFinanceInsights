"""
┌─────────────────────────────────────┐
│            SUMMARY MODULE           │
└─────────────────────────────────────┘
Summary endpoint functionality for Finance Insights

Provides text-only summary output of insights data with filtering capabilities.
"""

from fastapi import APIRouter
from fastapi.responses import Response
from typing import Optional
import items_management

# Create router for summary endpoints
summary_router = APIRouter(prefix="/summary", tags=["summary"])

@summary_router.get("")
async def get_summary(type_filter: Optional[str] = None, symbol_filter: Optional[str] = None):
    """
     ┌─────────────────────────────────────┐
     │            GET_SUMMARY              │
     └─────────────────────────────────────┘
     Text-only summary of insights table
     
     Returns a plain text representation of the insights table
     with all relevant information formatted for easy reading.
     
     Parameters:
     - type_filter: Optional feed type to filter insights by
     - symbol_filter: Optional symbol to filter insights by
     
     Returns:
     - Plain text summary of insights
    """
    insights = items_management.get_all_insights(type_filter=type_filter, symbol_filter=symbol_filter)
    
    # Filter insights with confidence > 50%
    high_confidence_insights = [
        insight for insight in insights 
        if insight.get('AIConfidence') is not None and insight.get('AIConfidence') > 0.5
    ]
    
    if not high_confidence_insights:
        return Response(content="No insights found with confidence > 50%.", media_type="text/plain")
    
    # Build text summary
    summary_lines = []
    summary_lines.append("JKB FINANCE INSIGHTS SUMMARY (CONFIDENCE > 50%)")
    summary_lines.append("=" * 60)
    
    if type_filter:
        summary_lines.append(f"Filtered by type: {type_filter}")
    if symbol_filter:
        summary_lines.append(f"Filtered by symbol: {symbol_filter}")
    
    summary_lines.append(f"Total insights: {len(high_confidence_insights)} (filtered from {len(insights)} total)")
    summary_lines.append("")
    
    for insight in high_confidence_insights:
        if insight.get('symbol'):
            summary_lines.append(f"Symbol: {insight['symbol']}")
        
        if insight.get('timePosted'):
            try:
                from datetime import datetime
                posted_time = datetime.fromisoformat(insight['timePosted'].replace('Z', '+00:00'))
                formatted_time = posted_time.strftime("%m-%d-%Y %H:%M")
                summary_lines.append(f"Posted: {formatted_time}")
            except:
                summary_lines.append(f"Posted: {insight['timePosted']}")
        
        if insight.get('AISummary'):
            summary_lines.append(f"{insight['AISummary']}")
        
        if insight.get('AIAction'):
            summary_lines.append(f"Proposed action: {insight['AIAction']}")
        
        if insight.get('AIConfidence') is not None:
            summary_lines.append(f"Confidence: {insight['AIConfidence']:.0%}")

        
        if insight.get('AILevels'):
            summary_lines.append(f"Levels (E: Entry, TP: Take Profit, SL: Stop Loss, S: Support, R: Resistance): {insight['AILevels']}")
        
        if insight.get('AIEventTime'):
            summary_lines.append(f"Event Time: {insight['AIEventTime']}")

        summary_lines.append("-" * 40)
    
    summary_text = "\n".join(summary_lines)
    return Response(content=summary_text, media_type="text/plain")
