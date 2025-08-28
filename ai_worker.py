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
from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_SUMMARY_MODEL, OPENAI_PROMPT1_ID, OPENAI_PROMPT1_VERSION_ID, OPENAI_PROMPT2_ID, OPENAI_PROMPT2_VERSION_ID
from debugger import debug_info, debug_warning, debug_error, debug_success

# Global OpenAI client instance
openai_client = None


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
    if not OPENAI_PROMPT1_ID or not OPENAI_PROMPT1_VERSION_ID:
        debug_error("Missing 'OPENAI_PROMPT1_ID' or 'OPENAI_PROMPT1_VERSION_ID' in configuration.")
        return None
    
    try:
        debug_info(f"OpenAI API Text Analysis initiated with prompt ID: {OPENAI_PROMPT1_ID} for {symbol} {item_type} {title}")
        
        # Create the API request using the template format
        response = client.responses.create(
            prompt={
                "id": OPENAI_PROMPT1_ID,
                "version": OPENAI_PROMPT1_VERSION_ID,
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
            "model": OPENAI_SUMMARY_MODEL,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": imageURL}}
                ]
            }],
        }
        
        # Make the API call
        debug_info(f"OpenAI API Image Analysis initiated with model: {OPENAI_SUMMARY_MODEL} for imageURL: {imageURL}")
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
        if "429" in error_msg or "quota" in error_msg.lower():
            debug_info("OpenAI quota exceeded. Check billing.")
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
        # Ensure OpenAI client is initialized and get the client instance
        client = openai_init()
        
        # Get configuration from config module
        from config import OPENAI_PROMPT2_ID, OPENAI_PROMPT2_VERSION_ID
        
        if not OPENAI_PROMPT2_ID or not OPENAI_PROMPT2_VERSION_ID:
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
        debug_info(f"OpenAI API Summary initiated with prompt ID: {OPENAI_PROMPT2_ID}")
        
        # Build prompt object
        prompt = {
            "id": OPENAI_PROMPT2_ID,
            "version": OPENAI_PROMPT2_VERSION_ID,
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
            
            # Support levels (array)
            if levels_data.get('support'):
                levels_summary.append(f"S: {', '.join(map(str, levels_data['support']))}")
            
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
        debug_error(f"OpenAI API Summary error in do_ai_summary: {str(e)}")
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
     Main AI analysis orchestrator with parallel execution
     
     Processes all insights that need AI analysis by:
     1. Finding insights with empty/null AISummary
     2. Running text and image analysis in parallel within each insight cluster
     3. Generating comprehensive summary after both analyses complete
     4. Updating database with results
     5. Processing multiple insights in parallel clusters
     
     Returns:
     - Tuple of (processed_count, success_count)
    """
    processed_count = 0
    success_count = 0
    
    try:
        # Get insights that need AI analysis
        insights = items_management.get_insights_for_ai()
        
        if not insights:
            debug_info("No insights need AI analysis. All insights have AISummary.")
            return processed_count, success_count
        
        debug_info(f"Found {len(insights)} insights needing AI analysis.")
        
        # Process insights in parallel clusters
        async def process_insight_cluster(insight):
            """Process a single insight with parallel text and image analysis"""
            insight_id = insight['id']
            try:
                debug_error(f"Processing insight #{insight_id}: {insight.get('title', 'Untitled')[:50]}...")
                
                # Set status to processing
                items_management.update_ai_analysis_status(insight_id, 'processing')
                
                # Get values from insight, ensuring they're strings
                symbol = insight.get('symbol') or ""
                item_type = insight.get('type') or ""
                title = insight.get('title') or ""
                content = insight.get('content') or ""
                image_url = insight.get('imageURL')
                
                debug_info(f"Symbol: {symbol}, Type: {item_type}")
                
                # New flow: first image analysis (if imageURL exists), then summary
                technical_analysis = ""
                
                # Step 1: Run image analysis if imageURL is valid
                if image_url and image_url != "" and image_url != "None":
                    debug_info(f"Running image analysis for URL: {image_url}")
                    try:
                        technical_analysis = await do_ai_image_analysis_async(symbol, image_url)
                        if technical_analysis:
                            items_management.update_insight(insight_id, AIImageSummary=technical_analysis)
                            debug_success(f"Image analysis complete for insight #{insight_id}")
                        else:
                            debug_warning(f"Image analysis returned empty for insight #{insight_id}")
                    except Exception as e:
                        debug_error(f"Image analysis failed: {str(e)}")
                        technical_analysis = ""
                else:
                    debug_info("No imageURL available, skipping image analysis")
                
                # Step 2: Run AI summary (always runs, uses technical_analysis if available)
                debug_info(f"Generating AI summary for insight #{insight_id}...")
                
                summary_data = await do_ai_summary_async(
                    symbol=symbol,
                    item_type=item_type,
                    title=title,
                    content=content,
                    technical=technical_analysis or ""  # Use empty string if no technical analysis
                )
                
                # Save all AI-generated fields
                if summary_data:
                    update_success = items_management.update_insight(
                        insight_id,
                        AISummary=summary_data.get('AISummary'),
                        AIAction=summary_data.get('AIAction'),
                        AIConfidence=summary_data.get('AIConfidence'),
                        AIEventTime=summary_data.get('AIEventTime'),
                        AILevels=summary_data.get('AILevels')
                    )
                    
                    if update_success:
                        # Set status to completed
                        items_management.update_ai_analysis_status(insight_id, 'completed')
                        debug_success(f"AI analysis complete for insight #{insight_id}")
                        return True
                    else:
                        # Set status to failed
                        items_management.update_ai_analysis_status(insight_id, 'failed')
                        debug_error(f"Failed to save AI analysis for insight #{insight_id}")
                        return False
                else:
                    # Set status to failed
                    items_management.update_ai_analysis_status(insight_id, 'failed')
                    debug_error(f"Failed to generate AI summary for insight #{insight_id}")
                    return False
                    
            except Exception as e:
                # Set status to failed
                items_management.update_ai_analysis_status(insight_id, 'failed')
                debug_error(f"Error processing insight #{insight_id}: {str(e)}")
                return False
        
        # Process all insights in parallel
        cluster_tasks = [process_insight_cluster(insight) for insight in insights]
        results = await asyncio.gather(*cluster_tasks, return_exceptions=True)
        
        # Count results
        processed_count = len(insights)
        success_count = sum(1 for result in results if result is True)
        
        debug_success(f"AI analysis complete: {success_count}/{processed_count} insights successfully analyzed.")
        
    except Exception as e:
        debug_error(f"Error during AI analysis: {str(e)}")
    
    return processed_count, success_count


# Test function
if __name__ == "__main__":
    debug_info("Testing AI Worker module...")
    debug_info("Note: AI methods are not yet implemented and will return None.")
    
    # Test the main analysis function
    processed, successful = do_ai_analysis()
    debug_info(f"\nResults: {processed} processed, {successful} successful.")
