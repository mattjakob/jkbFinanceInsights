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
            prompt = f"""You are an expert day trader. Analyze the attached image, which contains a technical analysis (TA) chart for {symbol} to extract a day trading strategy.
Return a {symbol} trading brief with:
- Focus on exressing a day trading hypothesis / strategy for {symbol} with clear indication of (bullish/bearish/neutral) in ≤30 words.  
- Identify overall direction (trendlines, channels, patterns).  
- Note key levels (support/resistance, breakouts, targets, stop-loss). 
- Infer timing: short-term = intraday; medium = 1–3 days; long = >1 week.
- Action: buy / sell / hold.
- Do not fabricate any information.
- Express full numeric values eg. 97k -> 97,000 USD
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
                    debug_info(f"OpenAI API Image Analysis responce ({len(analysis) if analysis else 0} chars)")
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


def do_ai_summary(text: str, technical: Optional[str], symbol: str, item_type: str) -> Dict[str, Any]:
    """
     ┌─────────────────────────────────────┐
     │         DO_AI_SUMMARY               │
     └─────────────────────────────────────┘
     Generate comprehensive AI summary and recommendations
     
     Combines text and technical analysis to produce actionable
     insights including summary, action, confidence, and levels.
     
     Parameters:
     - text: Text analysis summary from do_ai_text_analysis
     - technical: Technical/image analysis summary from do_ai_image_analysis (optional)
     - symbol: Stock symbol/ticker for context
     - item_type: Type of insight (e.g., "TD NEWS", "TD IDEAS RECENT")
     
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
            "symbol": symbol or "",
            "text_analysis": text or "",
            "technical_analysis": technical or ""
        }
        
        # Make the OpenAI Response API call
        debug_info(f"OpenAI API Summary initiated with prompt ID: {OPENAI_PROMPT2_ID}")
        response = client.responses.create(
            prompt={
                "id": OPENAI_PROMPT2_ID,
                "version": OPENAI_PROMPT2_VERSION_ID,
                "variables": variables
            }
        )
        
        # Extract the response content
        if hasattr(response, 'output_text') and response.output_text:
            summary_content = response.output_text
        else:
            debug_error("OpenAI API Summary failed: No 'output_text' in response.")
            return None
        
        debug_info(f"OpenAI API Summary received ({len(summary_content)} chars)")
        #debug_info(f"Response preview: {summary_content[:100]}...")
        
        # Parse the JSON response according to the schema
        try:
            import json
            parsed_data = json.loads(summary_content)
            
            # Extract data according to the schema
            summary = parsed_data.get('summary', '')
            action = parsed_data.get('action', 'hold').upper()  # Convert to uppercase to match enum
            confidence = parsed_data.get('confidence', 50) / 100.0  # Convert 0-100 to 0-1
            event_time = parsed_data.get('event_time')
            
            # Process levels data
            levels_data = parsed_data.get('levels', {})
            levels_summary = []
            
            if levels_data.get('support'):
                levels_summary.append(f"S: {', '.join(map(str, levels_data['support']))}")
            if levels_data.get('resistance'):
                levels_summary.append(f"R: {', '.join(map(str, levels_data['resistance']))}")
            if levels_data.get('targets'):
                levels_summary.append(f"T: {', '.join(map(str, levels_data['targets']))}")
            if levels_data.get('stop_loss'):
                levels_summary.append(f"SL: {levels_data['stop_loss']}")
            if levels_data.get('invalidation'):
                levels_summary.append(f"INV: {levels_data['invalidation']}")
            
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
                "AISummary": summary_content,
                "AIAction": "ANALYZE",
                "AIConfidence": 0.8,
                "AIEventTime": None,
                "AILevels": None
            }
        
    except Exception as e:
        debug_error(f"OpenAI API Summary error in do_ai_summary: {str(e)}")
        return None


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
                
                # Get values from insight, ensuring they're strings
                symbol = insight.get('symbol') or ""
                item_type = insight.get('type') or ""
                title = insight.get('title') or ""
                content = insight.get('content') or ""
                image_url = insight.get('imageURL')
                
                debug_info(f"Symbol: {symbol}, Type: {item_type}")
                
                # Run text and image analysis in parallel
                tasks = []
                
                # Always run text analysis
                text_task = asyncio.create_task(
                    do_ai_text_analysis_async(symbol, item_type, title, content)
                )
                tasks.append(('text', text_task))
                
                # Run image analysis only if imageURL is valid
                if image_url and image_url != "" and image_url != "None":
                    debug_info(f"Running image analysis for URL: {image_url}")
                    image_task = asyncio.create_task(
                        do_ai_image_analysis_async(symbol, image_url)
                    )
                    tasks.append(('image', image_task))
                else:
                    debug_info("Skipping image analysis. No valid imageURL.")
                
                # Wait for all analysis tasks to complete
                results = {}
                for task_type, task in tasks:
                    try:
                        result = await task
                        results[task_type] = result
                        
                        # Save individual analysis results
                        if task_type == 'text' and result:
                            items_management.update_insight(insight_id, AITextSummary=result)
                            debug_success(f"Text analysis complete. for insight #{insight_id}")
                        elif task_type == 'image' and result:
                            items_management.update_insight(insight_id, AIImageSummary=result)
                            debug_success(f"Image analysis complete. for insight #{insight_id}")
                        elif task_type == 'image' and not result:
                            debug_error(f"Image analysis failed or returned for insight #{insight_id}")
                            
                    except Exception as e:
                        debug_error(f"{task_type.capitalize()} analysis failed: {str(e)}")
                        results[task_type] = None
                
                # Generate comprehensive summary after both analyses complete
                debug_info(f"Generating AI summary for insight #{insight_id}...")
                text_analysis = results.get('text', "")
                image_analysis = results.get('image')
                
                summary_data = do_ai_summary(
                    text=text_analysis or "",
                    technical=image_analysis,
                    symbol=symbol,
                    item_type=item_type
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
                        debug_success(f"AI analysis complete for insight #{insight_id}")
                        return True
                    else:
                        debug_error(f"Failed to save AI analysis for insight #{insight_id}")
                        return False
                else:
                    debug_error(f"Failed to generate AI summary for insight #{insight_id}")
                    return False
                    
            except Exception as e:
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
