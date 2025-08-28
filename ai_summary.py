"""
┌─────────────────────────────────────┐
│         AI SUMMARY MODULE           │
└─────────────────────────────────────┘
AI-powered summary functionality for Finance Insights

Provides text-only summary output and AI-generated megasummary analysis.
"""

from fastapi import APIRouter
from fastapi.responses import Response
from typing import Optional
import items_management

# Create router for summary endpoints
summary_router = APIRouter(prefix="/summary", tags=["summary"])

@summary_router.post("/generate")
async def generate_ai_megasummary():
    """
     ┌─────────────────────────────────────┐
     │     GENERATE_AI_MEGASUMMARY        │
     └─────────────────────────────────────┘
     Generate AI-powered megasummary analysis
     
     Endpoint to trigger AI analysis of high-confidence insights.
     
     Returns:
     - AI-generated megasummary text
    """
    return await do_ai_megasummary()

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

async def do_ai_megasummary():
    """
     ┌─────────────────────────────────────┐
     │        DO_AI_MEGASUMMARY           │
     └─────────────────────────────────────┘
     Generate AI-powered megasummary analysis
     
     Calls the summary endpoint and sends results to OpenAI for enhanced analysis.
     Returns a comprehensive AI-generated summary of all high-confidence insights.
     
     Returns:
     - AI-generated megasummary text
    """
    try:
        # Call the summary endpoint internally
        from fastapi.testclient import TestClient
        from main import app
        
        client = TestClient(app)
        response = client.get("/summary")
        
        if response.status_code != 200:
            return "Error: Could not retrieve summary data"
        
        summary_text = response.text
        
        # Get OpenAI configuration from config
        from config import OPENAI_API_KEY, OPENAI_MODEL
        
        if not OPENAI_API_KEY:
            return "Error: OPENAI_API_KEY not configured in environment"
        
        # Prepare prompt for OpenAI
        prompt = f"""
        Analyze the following financial insights summary and provide a comprehensive analysis:

        {summary_text}

        Please provide:
        1. Overall market sentiment analysis
        2. Key trading opportunities identified
        3. Risk factors to consider
        4. Recommended portfolio positioning
        5. Timeline for expected moves

        Return a summary paragraph under 100 words and then a table in text format with key actions and levels.
        """
        
        # Use OpenAI client with different message roles
        from openai import OpenAI
        
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        try:
            response = client.responses.create(
                model="gpt-5",
                input=[
                    {
                        "role": "developer",
                        "content": "You are an expert day trader and technical analyst."
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": prompt}
                        ]
                    }
                ]
            )
            
            return response.output_text
            
        except Exception as openai_error:
            return f"Error calling OpenAI API: {str(openai_error)}"
                
    except Exception as e:
        return f"Error generating AI megasummary: {str(e)}"
