"""
/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │      TEXT REPORTS API ROUTES        │
 *  └─────────────────────────────────────┘
 *  API endpoints for generating text reports
 * 
 *  Provides endpoints for generating plain text reports
 *  of insights data for easy consumption.
 * 
 *  Parameters:
 *  - None
 * 
 *  Returns:
 *  - FastAPI router instance
 * 
 *  Notes:
 *  - Returns plain text responses
 *  - Suitable for terminal/CLI usage
 */
"""

from fastapi import APIRouter, Response
from datetime import datetime

from data import InsightsRepository
from debugger import debug_info, debug_error


# Create router
router = APIRouter(prefix="/api/summaries", tags=["summaries"])

# Repository instance
insights_repo = InsightsRepository()


@router.get("/{exchange_symbol}", response_class=Response)
async def get_symbol_text_report(exchange_symbol: str):
    """
     ┌─────────────────────────────────────┐
     │     GET_SYMBOL_TEXT_REPORT          │
     └─────────────────────────────────────┘
     Get plain text report for symbol insights
     
     Returns a formatted text report with AI analysis
     for all insights matching the symbol.
     
     Parameters:
     - exchange_symbol: Exchange:Symbol format (e.g., "NASDAQ:AAPL")
     
     Returns:
     - Plain text report
    """
    try:
        # Parse exchange:symbol format
        if ':' in exchange_symbol:
            exchange, symbol = exchange_symbol.split(':', 1)
            symbol = symbol.upper()
            exchange = exchange.upper()
        else:
            # Fallback: treat as just symbol
            symbol = exchange_symbol.upper()
            exchange = None
        
        # Get all insights for the symbol (only use symbol for filtering)
        insights = insights_repo.find_all(symbol_filter=symbol)
        
        if not insights:
            return Response(
                content=f"No insights found for symbol: {symbol.upper()}\n",
                media_type="text/plain"
            )
        
        # Filter insights with AI summaries
        insights_with_ai = [
            insight for insight in insights 
            if insight.ai_summary and insight.ai_summary.strip()
        ]
        
        if not insights_with_ai:
            return Response(
                content=f"No insights with AI analysis found for symbol: {symbol.upper()}\n",
                media_type="text/plain"
            )
        
        # Build the text report
        report_lines = []
        report_lines.append(f"INSIGHTS REPORT FOR {symbol}")
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Total summaries: {len(insights_with_ai)}")
        report_lines.append("")
        report_lines.append("")
        
        for insight in insights_with_ai:
            # Format date posted
            date_posted = insight.time_posted.strftime('%Y-%m-%d %H:%M:%S') if insight.time_posted else "Unknown"
            
            # Format confidence
            confidence = f"{insight.ai_confidence:.1%}" if insight.ai_confidence is not None else "N/A"
            
            # Get AI summary (already filtered to have one)
            ai_summary = insight.ai_summary.strip()
            
            # Get action
            action = insight.ai_action.value if insight.ai_action else "N/A"
            
            # Get event time
            event_time = insight.ai_event_time or "N/A"
            
            # Get levels
            levels = insight.ai_levels or "N/A"
            
            # Add insight to report
            report_lines.append("-" * 60)
            report_lines.append(f"Date posted: {date_posted}")
            report_lines.append(f"Confidence: {confidence}")
            report_lines.append(ai_summary)
            report_lines.append(f"Action: {action}")
            report_lines.append(f"Event Time: {event_time}")
            report_lines.append(f"Levels (E: Entry TP: Take Profit SL: Stop Loss S: Support R: Resistance): {levels}")
            report_lines.append("-" * 60)
            report_lines.append("")
        
        # Join all lines
        report_text = "\n".join(report_lines)
        
        debug_info(f"Generated text report for {symbol} with {len(insights)} insights")
        
        return Response(
            content=report_text,
            media_type="text/plain",
            headers={
                "Content-Disposition": f"inline; filename=report_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            }
        )
        
    except Exception as e:
        debug_error(f"Error generating report: {e}")
        return Response(
            content=f"Error generating report: {str(e)}\n",
            media_type="text/plain",
            status_code=500
        )
