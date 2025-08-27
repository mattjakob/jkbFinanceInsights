#!/usr/bin/env python3
"""
AI Worker module for analyzing financial insights

This module provides AI analysis functionality for financial insights,
including text analysis, image analysis, and comprehensive summary generation.
"""

from typing import Optional, Dict, Any, Tuple
import items_management
import os
from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_SUMMARY_MODEL, OPENAI_PROMPT1_ID, OPENAI_PROMPT1_VERSION_ID, OPENAI_PROMPT2_ID, OPENAI_PROMPT2_VERSION_ID

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
        print("Warning: OPENAI_API_KEY not found in environment variables")
        return None
    
    try:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        print("OpenAI client initialized successfully")
        return openai_client
    except Exception as e:
        print(f"Error initializing OpenAI client: {str(e)}")
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
        print("    Error: OpenAI client not initialized - check OPENAI_API_KEY")
        return None
    
    # Check if prompt configuration is available
    if not OPENAI_PROMPT1_ID or not OPENAI_PROMPT1_VERSION_ID:
        print("    Error: OPENAI_PROMPT1_ID or OPENAI_PROMPT1_VERSION_ID not configured in .env")
        return None
    
    try:
        print(f"    Making OpenAI API call with prompt ID: {OPENAI_PROMPT1_ID}")
        
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
        print(f"    Response received: {type(response)}")
        
        # Extract and return the analysis
        if hasattr(response, 'output_text') and response.output_text:
            analysis = response.output_text
            print(f"    Analysis content length: {len(analysis)}")
            print(f"    Analysis preview: {analysis[:100]}...")
            return analysis
        else:
            print(f"    Error: No output_text in response")
            print(f"    Response attributes: {[attr for attr in dir(response) if not attr.startswith('_')][:10]}")
            return None
            
    except Exception as e:
        error_msg = str(e)
        print(f"    Error during text analysis: {error_msg}")
        return None


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
        print("Error: OpenAI client not initialized - check OPENAI_API_KEY")
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
        print(f"    Making OpenAI API call to {OPENAI_SUMMARY_MODEL}...")
        response = client.chat.completions.create(**api_request)
        
        # Debug: Print response structure
        print(f"    Response received: {type(response)}")
        print(f"    Response choices: {len(response.choices) if response.choices else 0}")
        
        # Extract and return the analysis
        if response.choices and len(response.choices) > 0:
            choice = response.choices[0]
            print(f"    First choice type: {type(choice)}")
            print(f"    Choice message: {choice.message if hasattr(choice, 'message') else 'No message'}")
            
            if hasattr(choice, 'message') and choice.message:
                if hasattr(choice.message, 'content'):
                    analysis = choice.message.content
                    print(f"    Analysis content length: {len(analysis) if analysis else 0}")
                    print(f"    Analysis preview: {analysis[:100] if analysis else 'None'}...")
                    return analysis
                else:
                    print(f"    Error: Message has no content attribute")
                    return None
            else:
                print(f"    Error: Choice has no message")
                return None
        else:
            print(f"    Error: No choices in response")
            return None
            
    except Exception as e:
        error_msg = str(e)
        print(f"    Error during image analysis: {error_msg}")
        
        # Handle specific error types
        if "429" in error_msg or "quota" in error_msg.lower():
            print(f"    ⚠ OpenAI quota exceeded - check billing")
        elif "401" in error_msg or "unauthorized" in error_msg.lower():
            print(f"    ⚠ OpenAI API key invalid or expired")
        elif "400" in error_msg:
            print(f"    ⚠ Bad request - check image URL format")
        
        return None


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
            print("  ✗ Missing OpenAI prompt configuration")
            return None
        
        # Prepare variables for the API call
        variables = {
            "symbol": symbol or "",
            "text_analysis": text or "",
            "technical_analysis": technical or ""
        }
        
        # Make the OpenAI Response API call
        print(f"    Making OpenAI API call with prompt ID: {OPENAI_PROMPT2_ID}")
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
            print("  ✗ No output_text in OpenAI response")
            return None
        
        print(f"    Response content length: {len(summary_content)}")
        print(f"    Response preview: {summary_content[:100]}...")
        
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
            
            print(f"    Parsed data: Summary length={len(summary)}, Action={action}, Confidence={confidence}")
            
            return result_data
            
        except json.JSONDecodeError as e:
            print(f"  ✗ Failed to parse JSON response: {str(e)}")
            print(f"  Raw response: {summary_content[:200]}...")
            
            # Fallback to basic structure if JSON parsing fails
            return {
                "AISummary": summary_content,
                "AIAction": "ANALYZE",
                "AIConfidence": 0.8,
                "AIEventTime": None,
                "AILevels": None
            }
        
    except Exception as e:
        print(f"  ✗ Error in do_ai_summary: {str(e)}")
        return None


def do_ai_analysis() -> Tuple[int, int]:
    """
     ┌─────────────────────────────────────┐
     │         DO_AI_ANALYSIS              │
     └─────────────────────────────────────┘
     Main AI analysis orchestrator
     
     Processes all insights that need AI analysis by:
     1. Finding insights with empty/null AISummary
     2. Running text analysis on each insight
     3. Running image analysis if imageURL exists
     4. Generating comprehensive summary
     5. Updating database with results
     
     Returns:
     - Tuple of (processed_count, success_count)
    """
    processed_count = 0
    success_count = 0
    
    try:
        # Get insights that need AI analysis
        insights = items_management.get_insights_for_ai()
        
        if not insights:
            print("No insights need AI analysis - all insights already have AISummary")
            return processed_count, success_count
        
        print(f"Found {len(insights)} insights needing AI analysis")
        
        for insight in insights:
            processed_count += 1
            insight_id = insight['id']
            
            try:
                print(f"\nProcessing insight #{insight_id}: {insight.get('title', 'Untitled')[:50]}...")
                
                # Step 1: Perform text analysis
                print(f"  Running text analysis...")
                # Get values from insight, ensuring they're strings
                symbol = insight.get('symbol') or ""  # Use empty string if None
                item_type = insight.get('type') or ""  # This should already be a string like "TD IDEAS RECENT"
                title = insight.get('title') or ""
                content = insight.get('content') or ""
                
                print(f"    Symbol: {symbol}, Type: {item_type}")
                
                text_analysis = do_ai_text_analysis(
                    symbol=symbol,
                    item_type=item_type,
                    title=title,
                    content=content
                )
                
                # Save text analysis result
                if text_analysis:
                    items_management.update_insight(insight_id, AITextSummary=text_analysis)
                    print(f"  ✓ Text analysis complete")
                
                # Step 2: Perform image analysis if imageURL exists
                image_analysis = None
                image_url = insight.get('imageURL')
                if image_url and image_url != "" and image_url != "None":
                    print(f"  Running image analysis for URL: {image_url}")
                    image_analysis = do_ai_image_analysis(
                        symbol=insight.get('symbol'),
                        imageURL=image_url
                    )
                    
                    # Save image analysis result
                    if image_analysis:
                        items_management.update_insight(insight_id, AIImageSummary=image_analysis)
                        print(f"  ✓ Image analysis complete")
                    else:
                        print(f"  ⚠ Image analysis failed or returned None")
                else:
                    print(f"  ⏭ Skipping image analysis (no valid imageURL)")
                
                # Step 3: Generate comprehensive summary
                print(f"  Generating AI summary...")
                summary_data = do_ai_summary(
                    text=text_analysis or "",
                    technical=image_analysis,
                    symbol=symbol,
                    item_type=item_type
                )
                
                # Step 4: Save all AI-generated fields
                if summary_data:
                    update_success = items_management.update_insight_ai_fields(
                        insight_id,
                        AISummary=summary_data.get('AISummary'),
                        AIAction=summary_data.get('AIAction'),
                        AIConfidence=summary_data.get('AIConfidence'),
                        AIEventTime=summary_data.get('AIEventTime'),
                        AILevels=summary_data.get('AILevels')
                    )
                    
                    if update_success:
                        success_count += 1
                        print(f"  ✓ AI analysis complete for insight #{insight_id}")
                    else:
                        print(f"  ✗ Failed to save AI analysis for insight #{insight_id}")
                
            except Exception as e:
                print(f"  ✗ Error processing insight #{insight_id}: {str(e)}")
                continue
        
        print(f"\nAI analysis complete: {success_count}/{processed_count} insights successfully analyzed")
        
    except Exception as e:
        print(f"Error during AI analysis: {str(e)}")
    
    return processed_count, success_count


# Test function
if __name__ == "__main__":
    print("Testing AI Worker module...")
    print("Note: AI methods are not yet implemented and will return None")
    
    # Test the main analysis function
    processed, successful = do_ai_analysis()
    print(f"\nResults: {processed} processed, {successful} successful")
