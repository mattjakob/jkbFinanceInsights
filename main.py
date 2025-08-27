"""
┌─────────────────────────────────────┐
│         FINANCE INSIGHTS APP        │
└─────────────────────────────────────┘
Main FastAPI application for Finance Insights web app

A simple web application for managing finance-related insights with AI-generated
summaries and actions. Provides both API endpoints and web interface.
"""

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, StreamingResponse
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import sqlite3
from datetime import datetime
import json
from typing import Optional, List
import uvicorn
from pydantic import BaseModel
import items_management
import fake_data
import os
from symbol_validator import exchange_manager
from debugger import debugger, debug_info, debug_warning, debug_error, debug_success
from scrapers.tdNews_scraper import TradingViewNewsScraper
from scrapers.tdIdeasRecent_scraper import TradingViewIdeasRecentScraper
from scrapers.tdIdeasPopular_scraper import TradingViewIdeasPopularScraper
from scrapers.tdOpinions_scraper import TradingViewOpinionsScraper

class FetchRequest(BaseModel):
    symbol: str
    exchange: str
    feedType: str
    maxItems: int

# Initialize FastAPI app
app = FastAPI(title="Finance Insights", description="Simple Finance Insights Management App")

# Setup templates and static files
templates = Jinja2Templates(directory="templates")

# Custom static files with cache-busting for development
@app.get("/static/{file_path:path}")
async def serve_static_files(file_path: str, t: Optional[str] = None):
    """Serve static files with cache-busting headers for development"""
    file_path = os.path.join("static", file_path)
    if os.path.exists(file_path):
        return FileResponse(
            file_path,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    raise HTTPException(status_code=404, detail="File not found")

app.mount("/static", StaticFiles(directory="static"), name="static")

# Database schema
from database_schema import init_database, check_database_structure

class InsightCreate(BaseModel):
    """Data model for creating new insights"""
    type: str
    title: str
    content: str
    timePosted: Optional[str] = None
    symbol: Optional[str] = None
    exchange: Optional[str] = None
    imageURL: Optional[str] = None
    AITextSummary: Optional[str] = None
    AIImageSummary: Optional[str] = None
    AISummary: Optional[str] = None
    AIAction: Optional[str] = None
    AIConfidence: Optional[float] = None
    AIEventTime: Optional[str] = None
    AILevels: Optional[str] = None

class Insight(BaseModel):
    """Data model for insight responses"""
    id: int
    timeFetched: str
    timePosted: str
    type: str
    title: str
    content: str
    symbol: Optional[str] = None
    exchange: Optional[str] = None
    imageURL: Optional[str] = None
    AITextSummary: Optional[str] = None
    AIImageSummary: Optional[str] = None
    AISummary: Optional[str] = None
    AIAction: Optional[str] = None
    AIConfidence: Optional[float] = None
    AIEventTime: Optional[str] = None
    AILevels: Optional[str] = None

def init_db():
    """Initialize the database using the centralized schema module"""
    init_database()

# Database connection is now handled by database_schema module



# Initialize database on startup
init_db()

# Database structure checking is now handled by database_schema module

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, type_filter: Optional[str] = None):
    """
     ┌─────────────────────────────────────┐
     │             HOME                    │
     └─────────────────────────────────────┘
     Display the main page with all insights, optionally filtered by type
     
     Renders the home template with a list of all finance insights
     ordered by most recently posted first. Supports filtering by feed type.
     
     Parameters:
     - type_filter: Optional feed type to filter insights by
    """
    insights = items_management.get_all_insights(type_filter=type_filter)
    feed_names = items_management.get_feed_names()
    
    # Send debug message about page load
    filter_text = f" (filtered by: {type_filter})" if type_filter else ""
    #debug_info(f"Home page loaded with {len(insights)} insights{filter_text}")
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "insights": insights,
        "feed_names": feed_names,
        "selected_type": type_filter or ""
    })

@app.get("/add", response_class=HTMLResponse)
async def add_form(request: Request):
    """
     ┌─────────────────────────────────────┐
     │           ADD_FORM                  │
     └─────────────────────────────────────┘
     Display the form for adding new insights
     
     Renders the add insight form template for user input.
    """
    feed_names = items_management.get_feed_names()
    
    return templates.TemplateResponse("add.html", {
        "request": request,
        "feed_names": feed_names
    })

@app.post("/add")
async def add_insight(
    request: Request,
    type: str = Form(...),
    title: str = Form(...),
    content: str = Form(...),
    timePosted: Optional[str] = Form(None),
    symbol: Optional[str] = Form(None),
    exchange: Optional[str] = Form(None),
    imageURL: Optional[str] = Form(None),
    AITextSummary: Optional[str] = Form(None),
    AIImageSummary: Optional[str] = Form(None),
    AISummary: Optional[str] = Form(None),
    AIAction: Optional[str] = Form(None),
    AIConfidence: Optional[float] = Form(None),
    AIEventTime: Optional[str] = Form(None),
    AILevels: Optional[str] = Form(None)
):
    """
     ┌─────────────────────────────────────┐
     │         ADD_INSIGHT                 │
     └─────────────────────────────────────┘
     Add a new insight to the database
     
     Processes form data and creates a new insight record with current timestamps.
     Redirects to home page after successful creation.
    """
    try:
        # Process datetime fields
        if timePosted and timePosted.strip():
            try:
                dt = datetime.fromisoformat(timePosted)
                timePosted = dt.isoformat()
            except ValueError:
                timePosted = None
        else:
            timePosted = None
        
        if AIEventTime and AIEventTime.strip():
            try:
                dt = datetime.fromisoformat(AIEventTime)
                AIEventTime = dt.isoformat()
            except ValueError:
                AIEventTime = None
        else:
            AIEventTime = None
        
        # Use items_management to add the insight
        insight_id = items_management.add_insight(
            type=type,
            title=title,
            content=content,
            timePosted=timePosted,
            symbol=symbol,
            exchange=exchange,
            imageURL=imageURL,
            AITextSummary=AITextSummary,
            AIImageSummary=AIImageSummary,
            AISummary=AISummary,
            AIAction=AIAction,
            AIConfidence=AIConfidence,
            AIEventTime=AIEventTime,
            AILevels=AILevels
        )
        
        return RedirectResponse(url="/", status_code=303)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/edit-insight/{insight_id}", response_class=HTMLResponse)
async def edit_insight_form(request: Request, insight_id: int):
    """
     ┌─────────────────────────────────────┐
     │       EDIT_INSIGHT_FORM             │
     └─────────────────────────────────────┘
     Display edit form for a specific insight
     
     Shows a form pre-populated with current insight data for editing.
    """
    try:
        insight = items_management.get_insight_by_id(insight_id)
        if not insight:
            raise HTTPException(status_code=404, detail="Insight not found")
        
        feed_names = items_management.get_feed_names()
        
        return templates.TemplateResponse("edit.html", {
            "request": request,
            "insight": insight,
            "feed_names": feed_names
        })
    except Exception as e:
        debug_error(f"Error in edit_insight_form: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@app.post("/edit-insight/{insight_id}")
async def update_insight(
    request: Request,
    insight_id: int,
    type: str = Form(...),
    title: str = Form(...),
    content: str = Form(...),
    timePosted: Optional[str] = Form(None),
    symbol: Optional[str] = Form(None),
    exchange: Optional[str] = Form(None),
    imageURL: Optional[str] = Form(None),
    AITextSummary: Optional[str] = Form(None),
    AIImageSummary: Optional[str] = Form(None),
    AISummary: Optional[str] = Form(None),
    AIAction: Optional[str] = Form(None),
    AIConfidence: Optional[float] = Form(None),
    AIEventTime: Optional[str] = Form(None),
    AILevels: Optional[str] = Form(None)
):
    """
     ┌─────────────────────────────────────┐
     │         UPDATE_INSIGHT              │
     └─────────────────────────────────────┘
     Update an existing insight in the database
     
     Processes form data and updates the insight record.
     Redirects to detail page after successful update.
    """
    try:
        # Process datetime fields
        if timePosted and timePosted.strip():
            try:
                # The datetime-local input returns in format: YYYY-MM-DDTHH:MM
                # Convert to ISO format with seconds
                timePosted = timePosted + ":00"
            except:
                timePosted = None
        else:
            timePosted = None
            
        if AIEventTime and AIEventTime.strip():
            try:
                AIEventTime = AIEventTime + ":00"
            except:
                AIEventTime = None
        else:
            AIEventTime = None
        
        # Use items_management to update the insight
        success = items_management.update_insight(
            insight_id=insight_id,
            type=type,
            title=title,
            content=content,
            timePosted=timePosted,
            symbol=symbol,
            exchange=exchange,
            imageURL=imageURL,
            AITextSummary=AITextSummary,
            AIImageSummary=AIImageSummary,
            AISummary=AISummary,
            AIAction=AIAction,
            AIConfidence=AIConfidence,
            AIEventTime=AIEventTime,
            AILevels=AILevels
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Insight not found")
            
        return RedirectResponse(url=f"/insight/{insight_id}", status_code=303)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/insight/{insight_id}", response_class=HTMLResponse)
async def view_insight(request: Request, insight_id: int):
    """
     ┌─────────────────────────────────────┐
     │         VIEW_INSIGHT                │
     └─────────────────────────────────────┘
     Display detailed view of a specific insight
     
     Shows all fields of an insight including AI analysis data.
    """
    insight = items_management.get_insight_by_id(insight_id)
    
    if insight is None:
        raise HTTPException(status_code=404, detail="Insight not found")
    
    return templates.TemplateResponse("detail.html", {
        "request": request,
        "insight": insight
    })



@app.delete("/insight/{insight_id}")
async def delete_insight(insight_id: int):
    """
     ┌─────────────────────────────────────┐
     │       DELETE_INSIGHT                │
     └─────────────────────────────────────┘
     Delete an insight from the database
     
     Removes the specified insight record permanently.
    """
    success = items_management.delete_insight(insight_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Insight not found")
    
    return {"message": "Insight deleted successfully"}


# Debug stream endpoint to catch and log these requests
@app.get("/debug/stream")
async def debug_stream(request: Request):
    """Debug endpoint to catch stream requests and log them"""
    debug_warning(f"DEBUG STREAM REQUEST from {request.client.host}:{request.client.port}")
    return {"message": "Stream endpoint not implemented", "status": "debug"}  # Auto-reload test - working!

# Feed Names Management
@app.get("/api/feeds")
async def get_feeds():
    """
     ┌─────────────────────────────────────┐
     │           GET_FEEDS                 │
     └─────────────────────────────────────┘
     API endpoint to retrieve all feed names
     
     Returns a JSON list of all available feed names.
    """
    return items_management.get_feed_names()

# Feed creation is now handled by items_management module

# API Endpoints
@app.get("/api/insights", response_model=List[Insight])
async def get_insights():
    """
     ┌─────────────────────────────────────┐
     │         GET_INSIGHTS                │
     └─────────────────────────────────────┘
     API endpoint to retrieve all insights
     
     Returns a JSON list of all insights in the database.
    """
    return items_management.get_all_insights()

@app.post("/api/insights", response_model=Insight)
async def create_insight(insight: InsightCreate):
    """
     ┌─────────────────────────────────────┐
     │       CREATE_INSIGHT                │
     └─────────────────────────────────────┘
     API endpoint to create a new insight
     
     Accepts JSON data and creates a new insight record.
    """
    try:
        insight_id = items_management.add_insight(
            type=insight.type,
            title=insight.title,
            content=insight.content,
            timePosted=insight.timePosted,
            symbol=insight.symbol,
            exchange=insight.exchange,
            imageURL=insight.imageURL,
            AITextSummary=insight.AITextSummary,
            AIImageSummary=insight.AIImageSummary,
            AISummary=insight.AISummary,
            AIAction=insight.AIAction,
            AIConfidence=insight.AIConfidence,
            AIEventTime=insight.AIEventTime,
            AILevels=insight.AILevels
        )
        
        # Return the created insight
        created_insight = items_management.get_insight_by_id(insight_id)
        return created_insight
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/insights/analyze")
async def analyze_insights():
    """
     ┌─────────────────────────────────────┐
     │       UPDATE_MARKET_DATA            │
     └─────────────────────────────────────┘
     Update insights with AI analysis data
     
     Uses AI worker to analyze insights with empty AISummary,
     performing text analysis, image analysis, and generating
     comprehensive AI summaries with parallel execution.
    """
    try:
        from ai_worker import do_ai_analysis
        
        debug_info("Starting AI analysis for insights...")
        processed_count, success_count = await do_ai_analysis()
        
        if success_count > 0:
            debug_success(f"AI analysis completed: {success_count}/{processed_count} insights analyzed")
        else:
            debug_info("No insights needed AI analysis - all insights already processed")
        
        return {
            "success": True,
            "message": f"AI analysis complete: {success_count}/{processed_count} insights successfully analyzed",
            "processed_insights": processed_count,
            "updated_insights": success_count
        }
    except Exception as e:
        debug_error(f"AI analysis failed: {str(e)}")
        return {
            "success": False,
            "message": f"Error during AI analysis: {str(e)}"
        }

@app.get("/api/insights/analyze/stream")
async def analyze_insights_stream():
    """Stream AI analysis progress in real-time"""
    async def event_generator():
        try:
            from ai_worker import do_ai_analysis
            
            debug_info("Starting AI analysis stream...")
            processed_count, success_count = await do_ai_analysis()
            
            # Send final result
            yield f"data: {json.dumps({'type': 'complete', 'processed': processed_count, 'success': success_count})}\n\n"
            
        except Exception as e:
            debug_error(f"AI analysis stream failed: {str(e)}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )

@app.post("/api/insights/{insight_id}/reset-ai")
async def reset_insight_ai(insight_id: int):
    """
     ┌─────────────────────────────────────┐
     │        RESET_INSIGHT_AI             │
     └─────────────────────────────────────┘
     API endpoint to reset AI analysis fields for a specific insight
     
     Resets all AI-related fields (AISummary, AIAction, AIConfidence, 
     AIEventTime, AILevels) to null/empty for the specified insight.
     
     Parameters:
     - insight_id: The ID of the insight to reset AI fields for
     
     Returns:
     - JSON response with success status and message
    """
    try:
        # Check if insight exists
        insight = items_management.get_insight_by_id(insight_id)
        if not insight:
            return {
                "success": False,
                "message": f"Insight with ID {insight_id} not found"
            }
        
        # Reset the AI fields
        success = items_management.reset_insight_ai_fields(insight_id)
        
        if success:
            return {
                "success": True,
                "message": f"Successfully reset AI fields for insight #{insight_id}"
            }
        else:
            return {
                "success": False,
                "message": f"Failed to reset AI fields for insight #{insight_id}"
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"Error resetting AI fields: {str(e)}"
        }

@app.get("/api/symbols/search")
async def search_symbols(q: str, limit: int):
    """
     ┌─────────────────────────────────────┐
     │         SYMBOL_SEARCH               │
     └─────────────────────────────────────┘
     Search for trading symbols using TradingView API
     
     Provides autocomplete functionality by searching TradingView's symbol
     database and returning formatted results for frontend consumption.
     
     Parameters:
     - q: Search query (symbol name)
     - limit: Maximum number of results (default: 10)
     
     Returns:
     - JSON response with symbol suggestions and metadata
    """
    try:
        if not q or len(q.strip()) < 1:
            return {"symbols": []}
        
        # Use the exchange manager to search symbols
        results = exchange_manager.search_symbol(q.strip())
        
        # Format results for frontend
        formatted_results = []
        for result in results[:limit]:
            formatted_results.append({
                "symbol": result.symbol,
                "description": result.description,
                "type": result.type,
                "exchange": result.exchange,
                "currency": result.currency_code,
                "display_text": f"{result.symbol} - {result.description}",
                "is_primary": result.is_primary_listing
            })
        
        return {"symbols": formatted_results}
        
    except Exception as e:
        debug_error(f"Error searching symbols: {e}")
        return {"symbols": [], "error": str(e)}

class SymbolValidationRequest(BaseModel):
    symbol: str
    exchange: Optional[str] = None

@app.get("/api/symbols/validate")
async def validate_symbol(symbol: str, exchange: Optional[str] = None):
    """
     ┌─────────────────────────────────────┐
     │        VALIDATE_SYMBOL              │
     └─────────────────────────────────────┘
     Validate a trading symbol and get detailed information
     
     Uses TradingView API to validate symbol existence and format,
     returning comprehensive validation results and symbol metadata.
     
     Parameters:
     - request: JSON object containing symbol and optional exchange
     
     Returns:
     - JSON response with validation result and symbol details
    """
    try:
        if not symbol or len(symbol.strip()) < 1:
            return {"valid": False, "error": "Symbol is required"}
        
        # Use the exchange manager to validate
        validation_result = exchange_manager.validate_request(
            symbol=symbol.strip().upper(),
            exchange=exchange
        )
        
        return validation_result
        
    except Exception as e:
        debug_error(f"Error validating symbol: {e}")
        return {"valid": False, "error": str(e)}

@app.get("/api/debug-status")
async def get_debug_status():
    """
     ┌─────────────────────────────────────┐
     │        GET_DEBUG_STATUS             │
     └─────────────────────────────────────┘
     Get current debug status for frontend display
     
     Returns the current debug message and status from the debugger
     for display in the frontend status bar.
     
     Returns:
     - JSON response with current debug message and metadata
    """
    return debugger.get_current_status()

@app.delete("/api/insights")
async def delete_insights(type: str):
    """Delete insights by type"""
    try:
        # Handle empty type (delete all)
        if not type or type.strip() == "":
            debug_warning("Delete request for ALL insights")
            return {
                "success": False,
                "message": "Deleting all insights not implemented for safety"
            }
        
        debug_info(f"Delete request for type: {type}")
        result = items_management.delete_select_insights(type)
        
        if result["success"] and result["deleted_count"] > 0:
            debug_success(f"Deleted {result['deleted_count']} insights of type '{type}'")
        elif result["success"] and result["deleted_count"] == 0:
            debug_info(f"No insights found to delete for type '{type}'")
        else:
            debug_error(f"Delete operation failed: {result.get('message', 'Unknown error')}")
        
        return result
        
    except Exception as e:
        debug_error(f"Delete insights API failed: {str(e)}")
        return {
            "success": False,
            "message": f"Delete failed: {str(e)}"
        }





@app.post("/api/insights/fetch")
async def fetch_insights(request: FetchRequest):
    """
     ┌─────────────────────────────────────┐
     │         FETCH_DATA                  │
     └─────────────────────────────────────┘
     Fetch new insights from external data sources
     
     Uses the appropriate scraper based on feed type to retrieve new
     insights and create database entries.
     
     Parameters:
     - symbol: Trading symbol to fetch data for
     - exchange: Exchange name for the symbol
     - feedType: Type of feed to fetch (determines scraper to use)
     - maxItems: Maximum number of items to fetch
     
     Returns:
     - JSON response with fetch results and created insights
    """
    try:
        debug_info(f"Fetch data request: feedType='{request.feedType}' for {request.exchange}:{request.symbol} (max: {request.maxItems})")
        
        # Select the correct scraper based on feedType
        if request.feedType == "TD NEWS":
            debug_info("Using TradingViewNewsScraper")
            scraper = TradingViewNewsScraper()
        elif request.feedType == "TD IDEAS RECENT":
            debug_info("Using TradingViewIdeasRecentScraper")
            scraper = TradingViewIdeasRecentScraper()
        elif request.feedType == "TD IDEAS POPULAR":
            debug_info("Using TradingViewIdeasPopularScraper")
            scraper = TradingViewIdeasPopularScraper()
        elif request.feedType == "TD OPINIONS":
            debug_info("Using TradingViewOpinionsScraper")
            scraper = TradingViewOpinionsScraper()
        else:
            debug_error(f"Feed type '{request.feedType}' not implemented")
            return {
                "success": False,
                "message": f"Feed type '{request.feedType}' is not supported. Available types: TD NEWS, TD IDEAS RECENT, TD IDEAS POPULAR, TD OPINIONS",
                "processed_items": 0,
                "created_insights": 0,
                "failed_items": 0,
                "results": []
            }
        
        # Fetch data using the scraper
        results = scraper.fetch(
            symbol=request.symbol,
            exchange=request.exchange,
            maxItems=request.maxItems,
            sinceLast=None  # Not implemented yet
        )
        
        # Count successful creations
        successful_count = len([r for r in results if r.get("status") == "created"])
        failed_count = len(results) - successful_count
        
        if successful_count > 0:
            debug_success(f"Fetch completed: {successful_count} insights created")
        else:
            debug_warning(f"Fetch completed: no insights created ({failed_count} failed)")
        
        return {
            "success": True,
            "message": f"Fetch completed: {successful_count} insights created, {failed_count} failed",
            "processed_items": len(results),
            "created_insights": successful_count,
            "failed_items": failed_count,
            "results": results,
            "scraper_type": scraper.type,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        debug_error(f"Fetch data failed: {str(e)}")
        return {
            "success": False,
            "message": f"Fetch failed: {str(e)}",
            "processed_items": 0,
            "created_insights": 0,
            "failed_items": 0,
            "results": [],
            "timestamp": datetime.now().isoformat()
        }

@app.post("/api/insights/{insight_id}/ai-text-analysis")
async def ai_text_analysis(insight_id: int):
    """
     ┌─────────────────────────────────────┐
     │         AI_TEXT_ANALYSIS            │
     └─────────────────────────────────────┘
     Perform AI text analysis on an insight
     
     Analyzes the text content of an insight using OpenAI's
     text analysis capabilities and updates the AI fields.
     
     Parameters:
     - insight_id: ID of the insight to analyze
     
     Returns:
     - JSON response with analysis results
    """
    try:
        debug_info(f"AI text analysis requested for insight {insight_id}")
        
        # Get the insight from database
        insight = items_management.get_insight_by_id(insight_id)
        if not insight:
            raise HTTPException(status_code=404, detail="Insight not found")
        
        # Perform AI text analysis
        from ai_worker import do_ai_text_analysis
        analysis = do_ai_text_analysis(
            symbol=insight.get('symbol'),
            item_type=insight.get('type'),
            title=insight.get('title'),
            content=insight.get('content')
        )
        
        if analysis:
            # Update the insight with AI text analysis results
            items_management.update_insight(
                insight_id=insight_id,
                AITextSummary=analysis
            )
            
            # Run comprehensive AI summary with text analysis
            from ai_worker import do_ai_summary
            ai_summary_result = do_ai_summary(
                text=analysis,
                technical=None,  # No technical analysis for text-only
                symbol=insight.get('symbol', ''),
                item_type=insight.get('type', '')
            )
            
            if ai_summary_result:
                # Update AI fields with comprehensive summary
                items_management.update_insight_ai_fields(
                    insight_id=insight_id,
                    AISummary=ai_summary_result.get('AISummary'),
                    AIAction=ai_summary_result.get('AIAction'),
                    AIConfidence=ai_summary_result.get('AIConfidence'),
                    AIEventTime=ai_summary_result.get('AIEventTime'),
                    AILevels=ai_summary_result.get('AILevels')
                )
                debug_success(f"✓ AI text analysis and summary completed for insight {insight_id}")
            else:
                debug_warning(f"AI text analysis completed but summary generation failed for insight {insight_id}")
            
            return {
                "success": True,
                "message": "AI text analysis completed successfully",
                "AITextSummary": analysis,
                "insight_id": insight_id,
                "summary": ai_summary_result
            }
        else:
            debug_error(f"AI text analysis failed for insight {insight_id}")
            return {
                "success": False,
                "message": "AI text analysis failed",
                "insight_id": insight_id
            }
            
    except Exception as e:
        debug_error(f"AI text analysis error: {str(e)}")
        return {
            "success": False,
            "message": f"AI text analysis error: {str(e)}",
            "insight_id": insight_id,
            "error": str(e)
        }

@app.post("/api/insights/{insight_id}/ai-image-analysis")
async def ai_image_analysis(insight_id: int):
    """
     ┌─────────────────────────────────────┐
     │         AI_IMAGE_ANALYSIS           │
     └─────────────────────────────────────┘
     Perform AI image analysis on an insight
     
     Analyzes the image content of an insight using OpenAI's
     multimodal capabilities and updates the AI fields.
     
     Parameters:
     - insight_id: ID of the insight to analyze
     
     Returns:
     - JSON response with analysis results
    """
    try:
        debug_info(f"AI image analysis requested for insight {insight_id}")
        
        # Get the insight from database
        insight = items_management.get_insight_by_id(insight_id)
        if not insight:
            raise HTTPException(status_code=404, detail="Insight not found")
        
        # Check if insight has an image
        image_url = insight.get('imageURL')
        if not image_url:
            raise HTTPException(status_code=400, detail="Insight has no image to analyze")
        
        # Perform AI image analysis
        from ai_worker import do_ai_image_analysis
        analysis = do_ai_image_analysis(
            symbol=insight.get('symbol', ''),
            imageURL=image_url
        )
        
        if analysis:
            # Update the insight with AI image analysis results
            items_management.update_insight(
                insight_id=insight_id,
                AIImageSummary=analysis
            )
            
            # Get existing text analysis for comprehensive summary
            existing_text_analysis = insight.get('AITextSummary', '')
            
            # Run comprehensive AI summary with both text and image analysis
            from ai_worker import do_ai_summary
            ai_summary_result = do_ai_summary(
                text=existing_text_analysis,
                technical=analysis,  # Image analysis as technical analysis
                symbol=insight.get('symbol', ''),
                item_type=insight.get('type', '')
            )
            
            if ai_summary_result:
                # Update AI fields with comprehensive summary
                items_management.update_insight_ai_fields(
                    insight_id=insight_id,
                    AISummary=ai_summary_result.get('AISummary'),
                    AIAction=ai_summary_result.get('AIAction'),
                    AIConfidence=ai_summary_result.get('AIConfidence'),
                    AIEventTime=ai_summary_result.get('AIEventTime'),
                    AILevels=ai_summary_result.get('AILevels')
                )
                debug_success(f"✓ AI image analysis and summary completed for insight {insight_id}")
            else:
                debug_warning(f"AI image analysis completed but summary generation failed for insight {insight_id}")
            
            return {
                "success": True,
                "message": "AI image analysis completed successfully",
                "AIImageSummary": analysis,
                "insight_id": insight_id,
                "summary": ai_summary_result
            }
        else:
            debug_error(f"AI image analysis failed for insight {insight_id}")
            return {
                "success": False,
                "message": "AI image analysis failed",
                "insight_id": insight_id
            }
            
    except Exception as e:
        debug_error(f"AI image analysis error: {str(e)}")
        return {
            "success": False,
            "message": f"AI image analysis error: {str(e)}",
            "insight_id": insight_id,
            "error": str(e)
        }

if __name__ == "__main__":
    from config import SERVER_HOST, SERVER_PORT
    
    # Send initial debug message
    debug_success("Finance Insights server starting up...")
    
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)
