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

from services import InsightsService
from core import FeedType
from config import (
    FRONTEND_REFRESH_INTERVALS, APP_BEHAVIOR,
    TRADINGVIEW_CHART_HEIGHT, TRADINGVIEW_CHART_INTERVAL, 
    TRADINGVIEW_CHART_TIMEZONE
)

# Create router
router = APIRouter()

# Setup templates
templates = Jinja2Templates(directory="templates")

# Service instances
insights_service = InsightsService()


@router.get("/", response_class=HTMLResponse)
async def home(request: Request, type: Optional[str] = Query(None, description="Filter by feed type")):
    """
     ┌─────────────────────────────────────┐
     │             HOME                    │
     └─────────────────────────────────────┘
     Display the main web interface
     
     Shows all insights with optional type filtering.
    """
    # Clean type filter if provided
    clean_type = None
    if type:
        clean_type = type.replace('+', ' ').upper()
    
    # Get insights with optional type filter
    insights_data = insights_service.get_insights(type_filter=clean_type)
    
    # Get feed types for filter dropdown
    feed_names = [
        {"name": feed_type.value, "description": f"{feed_type.value} feed"}
        for feed_type in FeedType
    ]
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "insights": insights_data,
        "feed_names": feed_names,
        "selected_symbol": "",
        "selected_exchange": "",
        "selected_type": clean_type or "",
        "config": {
            "frontend_unified_refresh_interval": FRONTEND_REFRESH_INTERVALS["unified"],
            "frontend_age_refresh_interval": FRONTEND_REFRESH_INTERVALS["age"],
            "frontend_table_refresh_interval": FRONTEND_REFRESH_INTERVALS["table"],
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


@router.get("/api/insights/{exchange_symbol}", response_class=HTMLResponse)
async def insights_by_symbol(request: Request, exchange_symbol: str, type: Optional[str] = None):
    """
     ┌─────────────────────────────────────┐
     │      INSIGHTS BY EXCHANGE-SYMBOL    │
     └─────────────────────────────────────┘
     Display insights filtered by exchange and symbol
     
     Shows insights for a specific exchange-symbol combination.
     Also supports type filtering via query parameter for backward compatibility.
    """
    # Parse exchange-symbol format (e.g., "BINANCE:BTCUSD" -> exchange="BINANCE", symbol="BTCUSD")
    exchange = ""
    symbol = exchange_symbol.upper()
    
    if ':' in exchange_symbol:
        parts = exchange_symbol.split(':', 1)
        if len(parts) == 2:
            exchange = parts[0].upper()
            symbol = parts[1].upper()
    
    # Clean type filter if provided via query parameter
    clean_type = ""
    if type:
        clean_type = type.replace('+', ' ').upper()
    
    # Get filtered insights
    insights_data = insights_service.get_insights(
        symbol_filter=symbol, 
        type_filter=clean_type if clean_type else None
    )
    
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
        "config": {
            "frontend_unified_refresh_interval": FRONTEND_REFRESH_INTERVALS["unified"],
            "frontend_age_refresh_interval": FRONTEND_REFRESH_INTERVALS["age"],
            "frontend_table_refresh_interval": FRONTEND_REFRESH_INTERVALS["table"],
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


@router.get("/api/insights/{exchange_symbol}/{type_filter}", response_class=HTMLResponse)
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
        "config": {
            "frontend_unified_refresh_interval": FRONTEND_REFRESH_INTERVALS["unified"],
            "frontend_age_refresh_interval": FRONTEND_REFRESH_INTERVALS["age"],
            "frontend_table_refresh_interval": FRONTEND_REFRESH_INTERVALS["table"],
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
