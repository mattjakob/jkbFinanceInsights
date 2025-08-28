#!/usr/bin/env python3
"""
AI Worker module for analyzing financial insights

This module provides AI analysis functionality for financial insights,
including text analysis, image analysis, and comprehensive summary generation.
"""

from typing import Optional, Dict, Any, Tuple
import items_management
import os
import asyncio
import time
from datetime import datetime, timedelta
from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_IMAGEANALYSIS_MODEL, OPENAI_PROMPT_TEXTANALYSIS_ID, OPENAI_PROMPT_TEXTANALYSIS_VERSION_ID, OPENAI_PROMPT_BRIEFSTRATEGY_ID, OPENAI_PROMPT_BRIEFSTRATEGY_VERSION_ID, AI_CIRCUIT_BREAKER_THRESHOLD, AI_CIRCUIT_BREAKER_RESET_MINUTES
from debugger import debug_info, debug_warning, debug_error, debug_success

# Global OpenAI client instance
openai_client = None

# Circuit breaker for OpenAI API
_openai_circuit_breaker = {
    'is_open': False,
    'last_quota_error': None,
    'consecutive_quota_errors': 0,
    'quota_error_threshold': AI_CIRCUIT_BREAKER_THRESHOLD,  # Configurable threshold
    'reset_time_minutes': AI_CIRCUIT_BREAKER_RESET_MINUTES    # Configurable reset time
}


def _check_openai_circuit_breaker() -> bool:
    """
     ┌─────────────────────────────────────┐
     │    _CHECK_OPENAI_CIRCUIT_BREAKER    │
     └─────────────────────────────────────┘
     Check if OpenAI circuit breaker is open
     
     Returns True if circuit is open (should not call API)
    """
    if not _openai_circuit_breaker['is_open']:
        return False
        
    # Check if reset time has passed
    if _openai_circuit_breaker['last_quota_error']:
        reset_time = _openai_circuit_breaker['last_quota_error'] + timedelta(
            minutes=_openai_circuit_breaker['reset_time_minutes']
        )
        if datetime.now() > reset_time:
            # Reset circuit breaker
            _openai_circuit_breaker['is_open'] = False
            _openai_circuit_breaker['consecutive_quota_errors'] = 0
            debug_info("OpenAI circuit breaker reset - attempting API calls again")
            return False
    
    return True

def _handle_openai_quota_error():
    """Handle OpenAI quota error - update circuit breaker"""
    _openai_circuit_breaker['consecutive_quota_errors'] += 1
    _openai_circuit_breaker['last_quota_error'] = datetime.now()
    
    if _openai_circuit_breaker['consecutive_quota_errors'] >= _openai_circuit_breaker['quota_error_threshold']:
        _openai_circuit_breaker['is_open'] = True
        debug_error(f"OpenAI circuit breaker OPENED - too many quota errors ({_openai_circuit_breaker['consecutive_quota_errors']})")
        debug_info(f"Will retry OpenAI API calls after {_openai_circuit_breaker['reset_time_minutes']} minutes")

def _handle_openai_success():
    """Handle successful OpenAI API call - reset error counter"""
    if _openai_circuit_breaker['consecutive_quota_errors'] > 0:
        debug_info("OpenAI API call successful - resetting error counter")
        _openai_circuit_breaker['consecutive_quota_errors'] = 0

def openai_init() -> Optional[OpenAI]:
    """
     ┌─────────────────────────────────────┐
     │          OPENAI_INIT                │
     └─────────────────────────────────────┘
     Initialize OpenAI API connection
     
     Uses OPENAI_API_KEY from environment variables to create
     and return an OpenAI client instance.
     
     Returns:
     - OpenAI client instance if API key is available
     - None if API key is not configured
    """
    global openai_client
    
    if openai_client is not None:
        return openai_client
    
    if not OPENAI_API_KEY:
        debug_warning("Environment variable 'OPENAI_API_KEY' not found.")
        return None
    
    try:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        debug_success("OpenAI client initialized.")
        return openai_client
    except Exception as e:
        debug_error(f"Failed to initialize OpenAI client: {str(e)}")
        debug_error("OpenAI client not initialized. Check 'OPENAI_API_KEY'.")
        return None


# DEPRECATED: do_ai_text_analysis is no longer used
# The new flow uses do_ai_image_analysis (if imageURL exists) followed by do_ai_summary
'''
def do_ai_text_analysis(symbol: Optional[str], item_type: str, title: str, content: str) -> str:
    """
     ┌─────────────────────────────────────┐
     │        DO_AI_TEXT_ANALYSIS          │
     └─────────────────────────────────────┘
     Perform AI analysis on text content
     
     Analyzes the textual content of an insight including its
     symbol, type, title, and main content using OpenAI's
     response API with prompt templates.
     
     Parameters:
     - symbol: Stock symbol/ticker (optional)
     - item_type: Type of insight (e.g., TD IDEAS RECENT)
     - title: Title of the insight
     - content: Main content text to analyze
     
     Returns:
     - str: AI-generated text analysis summary
    """
    # Initialize OpenAI client if not already done
    client = openai_init()
    if not client:
        debug_error("OpenAI client not initialized. Check 'OPENAI_API_KEY'.")
        return None
    
    # Check if prompt configuration is available
    if not OPENAI_PROMPT_TEXTANALYSIS_ID or not OPENAI_PROMPT_TEXTANALYSIS_VERSION_ID:
        debug_error("Missing 'OPENAI_PROMPT_TEXTANALYSIS_ID' or 'OPENAI_PROMPT_TEXTANALYSIS_VERSION_ID' in configuration.")
        return None
    
    try:
        debug_info(f"OpenAI API Text Analysis initiated with prompt ID: {OPENAI_PROMPT_TEXTANALYSIS_ID} for {symbol} {item_type} {title}")
        
        # Create the API request using the template format
        response = client.responses.create(
            prompt={
                "id": OPENAI_PROMPT_TEXTANALYSIS_ID,
                "version": OPENAI_PROMPT_TEXTANALYSIS_VERSION_ID,
                "variables": {
                    "symbol": symbol,
                    "item_type": item_type,
                    "title": title,
                    "content": content
                }
            }
        )
        
        # Debug: Print response structure
        debug_info(f"OpenAI API Text Analysis response type: {type(response)}")
        
        # Extract and return the analysis
        if hasattr(response, 'output_text') and response.output_text:
            analysis = response.output_text
            debug_info(f"OpenAI API Text Analysis received ({len(analysis)} chars)")
            #debug_info(f"Analysis preview: {analysis[:100]}...")
            return analysis
        else:
            debug_error("OpenAI API Text Analysis failed: No 'output_text' in response.")
            #debug_error(f"OpenAI API Text Analysis response attributes: {[attr for attr in dir(response) if not attr.startswith('_')][:10]}")
            return None
            
    except Exception as e:
        error_msg = str(e)
        debug_error(f"OpenAI API Text Analysis error: {error_msg}")
        return None
'''


'''
async def do_ai_text_analysis_async(symbol: Optional[str], item_type: str, title: str, content: str) -> str:
    """
     ┌─────────────────────────────────────┐
     │   DO_AI_TEXT_ANALYSIS_ASYNC         │
     └─────────────────────────────────────┘
     Async wrapper for AI text analysis
     
     Wraps the synchronous text analysis function for use in async contexts.
     
     Parameters:
     - symbol: Stock symbol/ticker (optional)
     - item_type: Type of insight (e.g., TD IDEAS RECENT)
     - title: Title of the insight
     - content: Main content text to analyze
     
     Returns:
     - str: AI-generated text analysis summary
    """
    # Run the synchronous function in a thread pool to avoid blocking
    import asyncio
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, do_ai_text_analysis, symbol, item_type, title, content)
'''


def do_ai_image_analysis(symbol: str, imageURL: str) -> str:
    """
     ┌─────────────────────────────────────┐
     │       DO_AI_IMAGE_ANALYSIS          │
     └─────────────────────────────────────┘
     Perform AI analysis on image content
     
     Analyzes chart images or other visual content associated
     with the insight using OpenAI's multimodal API.
     
     Parameters:
     - symbol: Stock symbol/ticker (optional)
     - imageURL: URL of the image to analyze
     
     Returns:
     - str: AI-generated image analysis summary
    """
    # Check circuit breaker first
    if _check_openai_circuit_breaker():
        #debug_warning("OpenAI circuit breaker is open - skipping image analysis")
        return None
        
    # Initialize OpenAI client if not already done
    client = openai_init()
    if not client:
        debug_error("OpenAI client not initialized. Check 'OPENAI_API_KEY'.")
        return None
    
    try:
        # Prepare the prompt with symbol context if available
        prompt = "Analyze this financial chart/image"
        if symbol:
            prompt = f"""You are an expert day trader. Analyze the attached image, which contains a Technical Analysis chart for {symbol} to extract a day trading strategy.
Return a {symbol} trading brief with:
- Focus on exressing a day trading hypothesis / strategy for {symbol} with clear indication of (buy/sell/hold) action in ≤500 words.  
- Identify overall direction (trend lines, channels, patterns)
- Use OCR recognition if needed to understand notes
- Note key levels (Entry, Profit Taking, Stop-Loss, Support, Resistance)
- Determine if there's any imminent breakouts or trend reversals
- Infer timing: infer the most critical time to watch out for
- Do not fabricate any information.
- Express full numeric values eg. 97k -> 97,000 USD
- Ensure expecially the currency / price levels and timing information is consistent and accurate
- Go straight to the point and use a formal tone without filler words.
- If the image is not a chart or technical analysis, return "No chart found".
- If the technical analysis in the image is not clear or poorly executed shorten the analysis and add a note that it is not clear or poorly executed."""
        
        # Create the API request as specified
        api_request = {
            "model": OPENAI_IMAGEANALYSIS_MODEL,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": imageURL}}
                ]
            }],
        }
        
        # Make the API call
        debug_info(f"OpenAI API Image Analysis initiated with model: {OPENAI_IMAGEANALYSIS_MODEL} for imageURL: {imageURL}")
        response = client.chat.completions.create(**api_request)
        
        # Debug: Print response structure
        debug_info(f"OpenAI API Image Analysis response type: {type(response)}")
        #debug_info(f"Response choices: {len(response.choices) if response.choices else 0}")
        
        # Extract and return the analysis
        if response.choices and len(response.choices) > 0:
            choice = response.choices[0]
            #debug_info(f"First choice type: {type(choice)}")
            #debug_info(f"Choice message: {choice.message if hasattr(choice, 'message') else 'No message'}")
            
            if hasattr(choice, 'message') and choice.message:
                if hasattr(choice.message, 'content'):
                    analysis = choice.message.content
                    debug_info(f"OpenAI API Image Analysis response ({len(analysis) if analysis else 0} chars)")
                    #debug_info(f"Analysis preview: {analysis[:100] if analysis else 'None'}...")
                    _handle_openai_success()  # Reset circuit breaker on success
                    return analysis
                else:
                    debug_error("OpenAI API Image Analysis failed: Message has no 'content' attribute.")
                    return None
            else:
                debug_error("OpenAI API Image Analysis failed: Choice has no 'message'.")
                return None
        else:
            debug_error("OpenAI API Image Analysis failed: No choices in response.")
            return None
            
    except Exception as e:
        error_msg = str(e)
        debug_error(f"OpenAI API Image Analysis error: {error_msg}")
        
        # Handle specific error types
        if "429" in error_msg or "quota" in error_msg.lower() or "insufficient_quota" in error_msg.lower():
            debug_info("OpenAI quota exceeded. Check billing.")
            _handle_openai_quota_error()
        elif "401" in error_msg or "unauthorized" in error_msg.lower():
            debug_info("OpenAI API key invalid or expired.")
        elif "400" in error_msg:
            debug_info("Bad request. Check image URL format.")
        
        return None


async def do_ai_image_analysis_async(symbol: str, imageURL: str) -> str:
    """
     ┌─────────────────────────────────────┐
     │   DO_AI_IMAGE_ANALYSIS_ASYNC        │
     └─────────────────────────────────────┘
     Async wrapper for AI image analysis
     
     Wraps the synchronous image analysis function for use in async contexts.
     Returns None immediately if imageURL is empty/null to avoid unnecessary processing.
     
     Parameters:
     - symbol: Stock symbol/ticker
     - imageURL: URL of the image to analyze
     
     Returns:
     - str: AI-generated image analysis summary, or None if imageURL is invalid
    """
    # Early exit if imageURL is empty/null
    if not imageURL or imageURL == "" or imageURL == "None":
        return None
    
    # Run the synchronous function in a thread pool to avoid blocking
    import asyncio
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, do_ai_image_analysis, symbol, imageURL)


def do_ai_summary(
    symbol: str,
    item_type: str,
    title: str,
    content: str,
    technical: Optional[str] = None
) -> Dict[str, Any]:
    """
     ┌─────────────────────────────────────┐
     │         DO_AI_SUMMARY               │
     └─────────────────────────────────────┘
     Generate comprehensive AI summary and recommendations
     
     Analyzes insight content and optional technical analysis to produce
     actionable insights including summary, action, confidence, and levels.
     
     Parameters:
     - symbol: Stock symbol/ticker for context
     - item_type: Type of insight (e.g., "TD NEWS", "TD IDEAS RECENT")
     - title: Title of the insight
     - content: Main content text to analyze
     - technical: Technical/image analysis summary from do_ai_image_analysis (optional)
     
     Returns:
     - Dict containing:
       - AISummary: Comprehensive summary
       - AIAction: Recommended action (BUY/SELL/HOLD/WATCH)
       - AIConfidence: Confidence level (0-1)
       - AIEventTime: Predicted event timing
       - AILevels: Support/resistance levels
    """
    try:
        # Check circuit breaker first
        if _check_openai_circuit_breaker():
            debug_warning("OpenAI circuit breaker is open - skipping AI summary")
            return None
            
        # Ensure OpenAI client is initialized and get the client instance
        client = openai_init()
        
        # Get configuration from config module
        from config import OPENAI_PROMPT_BRIEFSTRATEGY_ID, OPENAI_PROMPT_BRIEFSTRATEGY_VERSION_ID
        
        if not OPENAI_PROMPT_BRIEFSTRATEGY_ID or not OPENAI_PROMPT_BRIEFSTRATEGY_VERSION_ID:
            debug_error("OpenAI API Summary failed: Missing OpenAI prompt configuration.")
            return None
        
        # Prepare variables for the API call
        variables = {
            "symbol": symbol,
            "item_type": item_type,
            "title": title,
            "content": content,
            "technical_analysis": technical or ""
        }
        
        debug_info(f"Variables prepared: symbol={symbol}, item_type={item_type}, title={title[:50]}...")
        
        # Make the OpenAI Response API call
        debug_info(f"OpenAI API Summary initiated with prompt ID: {OPENAI_PROMPT_BRIEFSTRATEGY_ID}")
        
        # Build prompt object
        prompt = {
            "id": OPENAI_PROMPT_BRIEFSTRATEGY_ID,
            "version": OPENAI_PROMPT_BRIEFSTRATEGY_VERSION_ID,
            "variables": variables
        }
        
        debug_info(f"Using prompt format: id={prompt['id']}, version={prompt['version']}")
        
        try:
            response = client.responses.create(prompt=prompt)
        except Exception as api_error:
            debug_error(f"OpenAI API call failed: {str(api_error)}")
            return None
        
        # Extract the response content
        if hasattr(response, 'output_text') and response.output_text:
            summary_content = response.output_text
        elif hasattr(response, 'text') and response.text:
            # Alternative field name
            summary_content = response.text
        elif hasattr(response, 'content') and response.content:
            # Another alternative field name
            summary_content = response.content
        else:
            debug_error(f"OpenAI API Summary failed: No recognized output field in response. Response attributes: {dir(response)}")
            return None
        
        debug_info(f"OpenAI API Summary received ({len(summary_content)} chars)")
        debug_info(f"Response preview: {summary_content[:200]}...")
        
        # Parse the JSON response according to the schema
        try:
            import json
            parsed_data = json.loads(summary_content)
            
            # Validate required fields according to schema
            required_fields = ['summary', 'action', 'confidence', 'event_time', 'levels']
            missing_fields = [field for field in required_fields if field not in parsed_data]
            if missing_fields:
                debug_warning(f"Response missing required fields: {missing_fields}")
            
            # Extract data according to the schema
            summary = parsed_data.get('summary', '')
            
            # Handle action enum (buy, sell, hold) - convert to uppercase for database
            action = parsed_data.get('action', 'hold').upper()
            if action not in ['BUY', 'SELL', 'HOLD']:
                debug_warning(f"Invalid action value: {action}, defaulting to HOLD")
                action = 'HOLD'
            
            confidence = parsed_data.get('confidence', 50) / 100.0  # Convert 0-100 to 0-1
            event_time = parsed_data.get('event_time')
            
            # Process levels data according to new schema
            levels_data = parsed_data.get('levels', {})
            levels_summary = []
            
            # Entry level
            if levels_data.get('entry') is not None:
                levels_summary.append(f"E: {levels_data['entry']}")
            
            # Take profit level
            if levels_data.get('take_profit') is not None:
                levels_summary.append(f"TP: {levels_data['take_profit']}")
            
            # Stop loss level
            if levels_data.get('stop_loss') is not None:
                levels_summary.append(f"SL: {levels_data['stop_loss']}")
            
            # Support levels (array or single value)
            if levels_data.get('support'):
                support = levels_data['support']
                if isinstance(support, (list, tuple)):
                    levels_summary.append(f"S: {', '.join(map(str, support))}")
                else:
                    levels_summary.append(f"S: {support}")
            
            # Resistance level (single value now, not array)
            if levels_data.get('resistance') is not None:
                levels_summary.append(f"R: {levels_data['resistance']}")
            
            ai_levels = " | ".join(levels_summary) if levels_summary else None
            
            # Create the return data structure
            result_data = {
                "AISummary": summary,
                "AIAction": action,
                "AIConfidence": confidence,
                "AIEventTime": event_time,
                "AILevels": ai_levels
            }
            
            debug_success("OpenAI API Summary parsed successfully.")
            _handle_openai_success()  # Reset circuit breaker on success
            
            return result_data
            
        except json.JSONDecodeError as e:
            debug_error(f"OpenAI API Summary failed to parse JSON: {str(e)}")
            debug_error(f"OpenAI API Summary raw response: {summary_content[:200]}...")
            
            # Fallback to basic structure if JSON parsing fails
            return {
                "AISummary": summary_content[:500] if len(summary_content) > 500 else summary_content,
                "AIAction": "HOLD",
                "AIConfidence": 0.5,
                "AIEventTime": None,
                "AILevels": None
            }
        
    except Exception as e:
        error_msg = str(e)
        debug_error(f"OpenAI API Summary error in do_ai_summary: {error_msg}")
        
        # Handle specific error types
        if "429" in error_msg or "quota" in error_msg.lower() or "insufficient_quota" in error_msg.lower():
            debug_info("OpenAI quota exceeded in summary. Check billing.")
            _handle_openai_quota_error()
        
        return None


async def do_ai_summary_async(
    symbol: str,
    item_type: str,
    title: str,
    content: str,
    technical: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
     ┌─────────────────────────────────────┐
     │      DO_AI_SUMMARY_ASYNC            │
     └─────────────────────────────────────┘
     Async wrapper for AI summary generation
     
     Wraps the synchronous summary function for use in async contexts.
     
     Parameters:
     - symbol: Stock symbol/ticker for context
     - item_type: Type of insight (e.g., TD IDEAS RECENT)
     - title: Title of the insight
     - content: Main content text to analyze
     - technical: Technical/image analysis summary (optional)
     
     Returns:
     - Dict with AI analysis fields or None if error
    """
    import asyncio
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, do_ai_summary, symbol, item_type, title, content, technical)


async def do_ai_analysis() -> Tuple[int, int]:
    """
     ┌─────────────────────────────────────┐
     │         DO_AI_ANALYSIS              │
     └─────────────────────────────────────┘
     Main AI analysis orchestrator using async task system
     
     Creates tasks for insights that need AI analysis and lets
     the background workers process them asynchronously.
     
     Returns:
     - Tuple of (insights_found, tasks_created)
    """
    from async_worker import create_ai_analysis_task
    
    insights_found = 0
    tasks_created = 0
    
    try:
        # Get insights that need AI analysis
        insights = items_management.get_insights_for_ai()
        
        if not insights:
            debug_info("No insights need AI analysis")
            return 0, 0
            
        insights_found = len(insights)
        debug_info(f"Found {insights_found} insights needing AI analysis")
        
        # Create tasks for each insight
        for insight in insights:
            try:
                num_tasks = await create_ai_analysis_task(insight['id'], insight)
                tasks_created += num_tasks
                debug_info(f"Created {num_tasks} tasks for insight #{insight['id']}")
            except Exception as e:
                debug_error(f"Failed to create tasks for insight #{insight['id']}: {str(e)}")
                # Update status to failed
                items_management.update_ai_analysis_status(insight['id'], 'failed')
        
        debug_success(f"Created {tasks_created} tasks for {insights_found} insights")
        
    except Exception as e:
        debug_error(f"Error during AI analysis task creation: {str(e)}")
    
    return insights_found, tasks_created


# Test function
if __name__ == "__main__":
    debug_info("Testing AI Worker module...")
    debug_info("Note: AI methods are not yet implemented and will return None.")
    
    # Test the main analysis function
    processed, successful = do_ai_analysis()
    debug_info(f"\nResults: {processed} processed, {successful} successful.")
