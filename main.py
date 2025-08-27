"""
┌─────────────────────────────────────┐
│         FINANCE INSIGHTS APP        │
└─────────────────────────────────────┘
Main FastAPI application for Finance Insights web app

A simple web application for managing finance-related insights with AI-generated
summaries and actions. Provides both API endpoints and web interface.
"""

from fastapi import FastAPI, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import sqlite3
from datetime import datetime
from typing import Optional, List
import uvicorn
from pydantic import BaseModel
import items_management
import fake_data

# Initialize FastAPI app
app = FastAPI(title="Finance Insights", description="Simple Finance Insights Management App")

# Setup templates and static files
templates = Jinja2Templates(directory="templates")
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
async def home(request: Request):
    """
     ┌─────────────────────────────────────┐
     │             HOME                    │
     └─────────────────────────────────────┘
     Display the main page with all insights
     
     Renders the home template with a list of all finance insights
     ordered by most recently posted first.
    """
    insights = items_management.get_all_insights()
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "insights": insights
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
        print(f"Error in edit_insight_form: {str(e)}")
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

# Debug endpoint
@app.get("/debug/feeds")
async def debug_feeds():
    """Debug endpoint to test feed names"""
    feeds = items_management.get_feed_names()
    return {"count": len(feeds), "feeds": feeds}

# Debug stream endpoint to catch and log these requests
@app.get("/debug/stream")
async def debug_stream(request: Request):
    """Debug endpoint to catch stream requests and log them"""
    import logging
    logging.warning(f"DEBUG STREAM REQUEST from {request.client.host}:{request.client.port}")
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

@app.post("/api/update-market-data")
async def update_market_data():
    """
     ┌─────────────────────────────────────┐
     │       UPDATE_MARKET_DATA            │
     └─────────────────────────────────────┘
     Update insights with AI analysis data
     
     Uses AI worker to analyze insights with empty AISummary,
     performing text analysis, image analysis, and generating
     comprehensive AI summaries.
    """
    try:
        from ai_worker import do_ai_analysis
        
        processed_count, success_count = do_ai_analysis()
        return {
            "success": True,
            "message": f"AI analysis complete: {success_count}/{processed_count} insights successfully analyzed",
            "processed_insights": processed_count,
            "updated_insights": success_count
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error during AI analysis: {str(e)}"
        }

if __name__ == "__main__":
    from config import SERVER_HOST, SERVER_PORT
    
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)
