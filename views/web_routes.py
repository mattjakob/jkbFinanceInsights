"""
/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │           WEB ROUTES                │
 *  └─────────────────────────────────────┘
 *  Web interface routes for HTML rendering
 * 
 *  Handles all web routes that render HTML templates
 *  for the user interface.
 * 
 *  Parameters:
 *  - None
 * 
 *  Returns:
 *  - FastAPI router with web routes
 * 
 *  Notes:
 *  - Uses services layer for business logic
 *  - Renders Jinja2 templates
 */
"""

from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse, RedirectResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from datetime import datetime
import re

from services import InsightManagementService, SymbolService
from core import FeedType
from data.repositories.reports import get_reports_repository
from tasks import get_task_queue
from config import (
    UI_REFRESH, FRONTEND_REFRESH_INTERVALS, APP_BEHAVIOR,
    TRADINGVIEW_CHART_HEIGHT, TRADINGVIEW_CHART_INTERVAL, 
    TRADINGVIEW_CHART_TIMEZONE
)

# Create router
router = APIRouter()

# Setup templates
templates = Jinja2Templates(directory="templates")

# Custom Jinja2 filters
def format_date_filter(date_string):
    """
    Format date string to 'ddd, mmm dd yyyy - hh:mm' format
    Example: '2025-08-29T22:24:52.911576' -> 'Friday, August 29 2025 - 10:24pm'
    """
    if not date_string or date_string == '-':
        return '-'
    
    try:
        # Parse ISO format datetime
        dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        
        # Format to desired output
        formatted = dt.strftime('%A, %B %d %Y - %I:%M%p')
        
        # Convert to lowercase for am/pm
        formatted = formatted.replace('AM', 'am').replace('PM', 'pm')
        
        return formatted
    except (ValueError, TypeError):
        # Return original if parsing fails
        return date_string

# Register the filter
templates.env.filters["format_date"] = format_date_filter

# Service instances
insights_service = InsightManagementService()
symbol_service = SymbolService()
reports_repo = get_reports_repository()


@router.get("/", response_class=HTMLResponse)
async def home(request: Request, 
               type: Optional[str] = Query(None, description="Filter by feed type"),
               symbol: Optional[str] = Query(None, description="Filter by symbol")):
    """
     ┌─────────────────────────────────────┐
     │             HOME                    │
     └─────────────────────────────────────┘
     Display the main web interface
     
     Shows all insights with optional type and symbol filtering.
    """
    # Parse symbol and exchange from symbol parameter
    exchange = ""
    symbol_filter = ""
    if symbol:
        if ':' in symbol:
            parts = symbol.split(':', 1)
            if len(parts) == 2:
                exchange = parts[0].upper()
                symbol_filter = parts[1].upper()
        else:
            symbol_filter = symbol.upper()
    
    # Clean type filter if provided
    clean_type = None
    if type:
        clean_type = type.replace('+', ' ').upper()
    
    # Get insights with optional filters
    insights_data = insights_service.get_insights(
        type_filter=clean_type,
        symbol_filter=symbol_filter
    )
    
    # Get feed types for filter dropdown
    feed_names = [
        {"name": feed_type.value, "description": f"{feed_type.value} feed"}
        for feed_type in FeedType
    ]
    
    # Get latest report for the symbol if provided
    latest_report = None
    if symbol_filter:
        latest_report = reports_repo.get_latest_by_symbol(symbol_filter)
    
    # Get actual task stats from queue
    task_queue = await get_task_queue()
    task_stats = await task_queue.get_stats()
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "insights": insights_data,
        "feed_names": feed_names,
        "selected_symbol": symbol_filter,
        "selected_exchange": exchange,
        "selected_type": clean_type or "",
        "latest_report": latest_report.to_dict() if latest_report else None,
        "current_time": datetime.now(),
        "task_stats": task_stats,
        "config": {
            "UI_REFRESH": UI_REFRESH,
            "frontend_unified_refresh_interval": FRONTEND_REFRESH_INTERVALS["unified"],
            "frontend_age_refresh_interval": FRONTEND_REFRESH_INTERVALS["age"],
            "UI_REFRESH_TABLE": FRONTEND_REFRESH_INTERVALS["table"],
            "frontend_status_refresh_interval": FRONTEND_REFRESH_INTERVALS["status"],
            "app_reload_delay": APP_BEHAVIOR["reload_delay"],
            "app_max_items": APP_BEHAVIOR["max_items"],
            "app_search_debounce": APP_BEHAVIOR["search_debounce"],
            "app_auto_refresh": APP_BEHAVIOR["auto_refresh"],
            "tradingview_chart_height": TRADINGVIEW_CHART_HEIGHT,
            "tradingview_chart_interval": TRADINGVIEW_CHART_INTERVAL,
            "tradingview_chart_timezone": TRADINGVIEW_CHART_TIMEZONE
        }
    })


@router.get("/reports", response_class=HTMLResponse)
async def reports(request: Request, symbol: Optional[str] = Query(None, description="Filter by symbol"), 
                  status: Optional[str] = Query(None, description="Filter by status"),
                  time_range: Optional[str] = Query("all", description="Time range in hours")):
    """
     ┌─────────────────────────────────────┘
     │            REPORTS                  │
     └─────────────────────────────────────┘
     Display AI analysis reports
     
     Shows all AI analysis reports with optional filtering.
    """
    try:
        # Get reports with optional filters
        if time_range and time_range != "all":
            try:
                hours = int(time_range)
                reports_data = reports_repo.get_recent(hours=hours)
            except ValueError:
                reports_data = reports_repo.get_recent(hours=24)
        else:
            reports_data = reports_repo.get_all(limit=250)
        
        # Apply additional filters if provided
        if symbol:
            symbol = symbol.upper()
            reports_data = [r for r in reports_data if r.symbol == symbol]
        
        if status:
            reports_data = [r for r in reports_data if r.ai_task.status.value == status]
        
        # Convert to dict format for template
        reports_dict = [r.to_dict() for r in reports_data]
        
        return templates.TemplateResponse("reports.html", {
            "request": request,
            "reports": reports_dict,
            "selected_symbol": symbol or "",
            "selected_status": status or "",
            "selected_time_range": time_range or "all",
            "config": {
                "frontend_unified_refresh_interval": FRONTEND_REFRESH_INTERVALS["unified"],
                "frontend_age_refresh_interval": FRONTEND_REFRESH_INTERVALS["age"],
                "UI_REFRESH_TABLE": FRONTEND_REFRESH_INTERVALS["table"],
                "frontend_status_refresh_interval": FRONTEND_REFRESH_INTERVALS["status"],
                "app_reload_delay": APP_BEHAVIOR["reload_delay"],
                "app_max_items": APP_BEHAVIOR["max_items"],
                "app_search_debounce": APP_BEHAVIOR["search_debounce"],
                "app_auto_refresh": APP_BEHAVIOR["auto_refresh"],
                "tradingview_chart_height": TRADINGVIEW_CHART_HEIGHT,
                "tradingview_chart_interval": TRADINGVIEW_CHART_INTERVAL,
                "tradingview_chart_timezone": TRADINGVIEW_CHART_TIMEZONE
            }
        })
    except Exception as e:
        from debugger import debug_error
        debug_error(f"Error in reports route: {str(e)}")
        # Return empty reports on error
        return templates.TemplateResponse("reports.html", {
            "request": request,
            "reports": [],
            "selected_symbol": "",
            "selected_status": "",
            "selected_time_range": "24",
            "config": {
                "frontend_unified_refresh_interval": FRONTEND_REFRESH_INTERVALS["unified"],
                "frontend_age_refresh_interval": FRONTEND_REFRESH_INTERVALS["age"],
                "UI_REFRESH_TABLE": FRONTEND_REFRESH_INTERVALS["table"],
                "frontend_status_refresh_interval": FRONTEND_REFRESH_INTERVALS["status"],
                "app_reload_delay": APP_BEHAVIOR["reload_delay"],
                "app_max_items": APP_BEHAVIOR["max_items"],
                "app_search_debounce": APP_BEHAVIOR["search_debounce"],
                "app_auto_refresh": APP_BEHAVIOR["auto_refresh"],
                "tradingview_chart_height": TRADINGVIEW_CHART_HEIGHT,
                "tradingview_chart_interval": TRADINGVIEW_CHART_INTERVAL,
                "tradingview_chart_timezone": TRADINGVIEW_CHART_TIMEZONE
            }
        })





@router.get("/web/insights/{exchange_symbol}/{type_filter}", response_class=HTMLResponse)
async def insights_by_symbol_and_type(request: Request, exchange_symbol: str, type_filter: str):
    """
     ┌─────────────────────────────────────┐
     │ INSIGHTS BY EXCHANGE-SYMBOL AND TYPE│
     └─────────────────────────────────────┘
     Display insights filtered by exchange, symbol and type
     
     Shows insights for a specific exchange-symbol combination and feed type.
    """
    # Parse exchange-symbol format (e.g., "BINANCE:BTCUSD" -> exchange="BINANCE", symbol="BTCUSD")
    exchange = ""
    symbol = exchange_symbol.upper()
    
    if ':' in exchange_symbol:
        parts = exchange_symbol.split(':', 1)
        if len(parts) == 2:
            exchange = parts[0].upper()
            symbol = parts[1].upper()
    
    # Clean type filter - replace underscores with spaces
    clean_type = type_filter.replace('_', ' ').upper()
    
    # Get filtered insights
    insights_data = insights_service.get_insights(
        symbol_filter=symbol, 
        type_filter=clean_type
    )
    
    # Get latest report for the symbol
    latest_report = None
    if symbol:
        latest_report = reports_repo.get_latest_by_symbol(symbol)
    
    # Get feed types for filter dropdown
    feed_names = [
        {"name": feed_type.value, "description": f"{feed_type.value} feed"}
        for feed_type in FeedType
    ]
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "insights": insights_data,
        "feed_names": feed_names,
        "selected_symbol": symbol,
        "selected_exchange": exchange,
        "selected_type": clean_type,
        "latest_report": latest_report.to_dict() if latest_report else None,
        "current_time": datetime.now(),
        "task_stats": {"processing": 0, "pending": 0, "completed": 0, "failed": 0},
        "config": {
            "UI_REFRESH": UI_REFRESH,
            "frontend_unified_refresh_interval": FRONTEND_REFRESH_INTERVALS["unified"],
            "frontend_age_refresh_interval": FRONTEND_REFRESH_INTERVALS["age"],
            "UI_REFRESH_TABLE": FRONTEND_REFRESH_INTERVALS["table"],
            "frontend_status_refresh_interval": FRONTEND_REFRESH_INTERVALS["status"],
            "app_reload_delay": APP_BEHAVIOR["reload_delay"],
            "app_max_items": APP_BEHAVIOR["max_items"],
            "app_search_debounce": APP_BEHAVIOR["search_debounce"],
            "app_auto_refresh": APP_BEHAVIOR["auto_refresh"],
            "tradingview_chart_height": TRADINGVIEW_CHART_HEIGHT,
            "tradingview_chart_interval": TRADINGVIEW_CHART_INTERVAL,
            "tradingview_chart_timezone": TRADINGVIEW_CHART_TIMEZONE
        }
    })


@router.get("/insight/{insight_id}", response_class=HTMLResponse)
async def view_insight(request: Request, insight_id: int):
    """
     ┌─────────────────────────────────────┐
     │         VIEW_INSIGHT                │
     └─────────────────────────────────────┘
     Display detailed view of an insight
    """
    insight_data = insights_service.get_insight_by_id(insight_id)
    
    if not insight_data:
        return RedirectResponse(url="/", status_code=404)
    
    return templates.TemplateResponse("detail.html", {
        "request": request,
        "insight": insight_data
    })


@router.get("/add", response_class=HTMLResponse)
async def add_form(request: Request):
    """Display form for adding insights (testing)"""
    feed_names = [
        {"name": feed_type.value, "description": f"{feed_type.value} feed"}
        for feed_type in FeedType
    ]
    
    return templates.TemplateResponse("add.html", {
        "request": request,
        "feed_names": feed_names
    })


@router.get("/edit-insight/{insight_id}", response_class=HTMLResponse)
async def edit_form(request: Request, insight_id: int):
    """Display form for editing an insight"""
    insight_data = insights_service.get_insight_by_id(insight_id)
    
    if not insight_data:
        return RedirectResponse(url="/", status_code=404)
    
    feed_names = [
        {"name": feed_type.value, "description": f"{feed_type.value} feed"}
        for feed_type in FeedType
    ]
    
    return templates.TemplateResponse("edit.html", {
        "request": request,
        "insight": insight_data,
        "feed_names": feed_names
    })


@router.get("/summary")
async def get_summary():
    """Get text summary of all high-confidence insights"""
    insights_data = insights_service.get_insights()
    
    # Filter high confidence
    high_confidence = [
        i for i in insights_data 
        if i.get('AIConfidence') and i['AIConfidence'] > 0.5
    ]
    
    if not high_confidence:
        return PlainTextResponse("No insights found with confidence > 50%.")
    
    # Build text summary
    lines = []
    lines.append("JKB FINANCE INSIGHTS SUMMARY (CONFIDENCE > 50%)")
    lines.append("=" * 60)
    lines.append(f"Total insights: {len(high_confidence)}")
    lines.append("")
    
    for insight in high_confidence:
        if insight.get('symbol'):
            lines.append(f"Symbol: {insight['symbol']}")
        
        if insight.get('timePosted'):
            lines.append(f"Posted: {insight['timePosted']}")
        
        if insight.get('AISummary'):
            lines.append(insight['AISummary'])
        
        if insight.get('AIAction'):
            lines.append(f"Proposed action: {insight['AIAction']}")
        
        if insight.get('AIConfidence'):
            lines.append(f"Confidence: {insight['AIConfidence']:.0%}")
        
        if insight.get('AILevels'):
            lines.append(f"Levels: {insight['AILevels']}")
        
        if insight.get('AIEventTime'):
            lines.append(f"Event Time: {insight['AIEventTime']}")
        
        lines.append("-" * 40)
    
    return PlainTextResponse("\n".join(lines))


@router.get("/summary/{exchange_symbol}")
async def get_summary_by_symbol(exchange_symbol: str):
    """Get text summary of high-confidence insights for an exchange-symbol combination"""
    # Parse exchange-symbol format
    exchange = ""
    symbol = exchange_symbol.upper()
    
    if ':' in exchange_symbol:
        parts = exchange_symbol.split(':', 1)
        if len(parts) == 2:
            exchange = parts[0].upper()
            symbol = parts[1].upper()
    
    insights_data = insights_service.get_insights(symbol_filter=symbol)
    
    # Filter high confidence
    high_confidence = [
        i for i in insights_data 
        if i.get('AIConfidence') and i['AIConfidence'] > 0.5
    ]
    
    if not high_confidence:
        return PlainTextResponse(f"No insights found for {exchange}:{symbol} with confidence > 50%.")
    
    # Build text summary
    lines = []
    lines.append(f"JKB FINANCE INSIGHTS SUMMARY - {exchange}:{symbol} (CONFIDENCE > 50%)")
    lines.append("=" * 60)
    lines.append(f"Total insights: {len(high_confidence)}")
    lines.append("")
    
    for insight in high_confidence:
        if insight.get('timePosted'):
            lines.append(f"Posted: {insight['timePosted']}")
        
        if insight.get('AISummary'):
            lines.append(insight['AISummary'])
        
        if insight.get('AIAction'):
            lines.append(f"Proposed action: {insight['AIAction']}")
        
        if insight.get('AIConfidence'):
            lines.append(f"Confidence: {insight['AIConfidence']:.0%}")
        
        if insight.get('AILevels'):
            lines.append(f"Levels: {insight['AILevels']}")
        
        if insight.get('AIEventTime'):
            lines.append(f"Event Time: {insight['AIEventTime']}")
        
        lines.append("-" * 40)
    
    return PlainTextResponse("\n".join(lines))
