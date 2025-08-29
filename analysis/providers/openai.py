"""
/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │        OPENAI PROVIDER              │
 *  └─────────────────────────────────────┘
 *  OpenAI implementation of AI provider
 * 
 *  Implements the AI provider interface using OpenAI's API
 *  for text and image analysis.
 * 
 *  Parameters:
 *  - None
 * 
 *  Returns:
 *  - OpenAIProvider instance
 * 
 *  Notes:
 *  - Requires OPENAI_API_KEY in environment
 *  - Supports GPT-4 and vision models
 */
"""

import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import asyncio

import time
from openai import AsyncOpenAI, OpenAI

from .base import AIProvider
from ..models import AnalysisRequest, ImageAnalysisRequest, AnalysisResult, AnalysisAction
from config import (
    OPENAI_API_KEY, OPENAI_MODEL,
    OPENAI_PROMPT_BRIEFSTRATEGY_ID, OPENAI_PROMPT_BRIEFSTRATEGY_VERSION_ID,
    OPENAI_PROMPT_REPORT_ID, OPENAI_PROMPT_REPORT_VERSION_ID,
    OPENAI_TIMEOUT, OPENAI_RATE_LIMIT
)
from debugger import debug_info, debug_error, debug_warning, debug_success


class RateLimiter:
    """Simple rate limiter to prevent API overload"""
    
    def __init__(self, max_calls_per_minute: int = 10):
        self.max_calls_per_minute = max_calls_per_minute
        self.calls = []
        self.min_delay_between_calls = 1.0  # Minimum 1 second between calls
        self.last_call_time = 0
    
    async def wait_if_needed(self):
        """Wait if we're hitting rate limits"""
        now = time.time()
        
        # Ensure minimum delay between calls
        time_since_last_call = now - self.last_call_time
        if time_since_last_call < self.min_delay_between_calls:
            delay = self.min_delay_between_calls - time_since_last_call
            debug_info(f"Rate limiter: waiting {delay:.2f}s before next call")
            await asyncio.sleep(delay)
            now = time.time()
        
        # Remove calls older than 1 minute
        self.calls = [call_time for call_time in self.calls if now - call_time < 60]
        
        # If we've hit the limit, wait
        if len(self.calls) >= self.max_calls_per_minute:
            wait_time = 60 - (now - self.calls[0]) + 1
            debug_warning(f"Rate limit reached ({self.max_calls_per_minute} calls/min), waiting {wait_time:.2f}s")
            await asyncio.sleep(wait_time)
            # Clean up old calls after waiting
            now = time.time()
            self.calls = [call_time for call_time in self.calls if now - call_time < 60]
        
        # Record this call
        self.calls.append(now)
        self.last_call_time = now
    
    def get_wait_time(self) -> float:
        """Get wait time needed for rate limiting (sync version)"""
        now = time.time()
        if self.last_call_time is None:
            self.last_call_time = now
            return 0.0
        
        time_since_last = now - self.last_call_time
        min_interval = 60.0 / self.max_calls_per_minute
        
        if time_since_last < min_interval:
            wait_time = min_interval - time_since_last
            self.last_call_time = now + wait_time
            return wait_time
        
        self.last_call_time = now
        return 0.0



class OpenAIProvider(AIProvider):
    """
     ┌─────────────────────────────────────┐
     │       OPENAIPROVIDER                │
     └─────────────────────────────────────┘
     OpenAI implementation of AI provider
     
     Uses OpenAI's API for financial analysis.
    """
    
    def __init__(self):
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not configured")
        
        # Keep sync client for backward compatibility
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        # Add async client for proper async operations
        self.async_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        # Add rate limiter using config value
        self.rate_limiter = RateLimiter(max_calls_per_minute=OPENAI_RATE_LIMIT)
    
    def analyze_text(self, request: AnalysisRequest) -> AnalysisResult:
        """
         ┌─────────────────────────────────────┐
         │        ANALYZE_TEXT                 │
         └─────────────────────────────────────┘
         Analyze text using OpenAI
         
         Uses the configured prompt template for structured
         financial analysis.
        """
        # Note: Sync version kept for backward compatibility but should use async version
        # This method uses blocking sleep which can cause server stuttering
        debug_warning("Using synchronous OpenAI call - consider using async version")
        
        try:
            # Use prompt template if configured
            if OPENAI_PROMPT_BRIEFSTRATEGY_ID and OPENAI_PROMPT_BRIEFSTRATEGY_VERSION_ID:
                response = self._call_with_template(request)
            else:
                response = self._call_direct(request)
            
            # Parse response
            result = self._parse_response(response)
            return result
            
        except Exception as e:
            raise
    
    def analyze_image(self, request: ImageAnalysisRequest) -> str:
        """
         ┌─────────────────────────────────────┐
         │       ANALYZE_IMAGE                 │
         └─────────────────────────────────────┘
         Analyze image using OpenAI Vision
         
         Extracts trading strategy from chart images.
        """
        # Note: Sync version kept for backward compatibility but should use async version
        # This method uses blocking sleep which can cause server stuttering
        debug_warning("Using synchronous OpenAI call - consider using async version")
        
        try:
            prompt = self._build_image_prompt(request.symbol)
            
            response = self.client.responses.create(
                model=OPENAI_MODEL,
                input=[
                    {
                        "role": "developer",
                        "content": "You are an expert day trader and technical analyst."
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": prompt},
                            {"type": "input_image", "image_url": request.image_url}
                        ]
                    }
                ]
            )
            
            analysis = response.output_text
            debug_info(f"Image analysis completed ({len(analysis)} chars)")
            
            return analysis
            
        except Exception as e:
            raise
    
    def _call_with_template(self, request: AnalysisRequest) -> str:
        """Call OpenAI using prompt template"""
        prompt = {
            "id": OPENAI_PROMPT_BRIEFSTRATEGY_ID,
            "version": OPENAI_PROMPT_BRIEFSTRATEGY_VERSION_ID,
            "variables": {
                "symbol": request.symbol,
                "item_type": request.item_type,
                "title": request.title,
                "content": request.text,
                "technical_analysis": request.technical
            }
        }
        
        response = self.client.responses.create(prompt=prompt)
        
        if hasattr(response, 'output_text') and response.output_text:
            return response.output_text
        elif hasattr(response, 'text') and response.text:
            return response.text
        else:
            raise ValueError("No output in OpenAI response")
    
    def _call_direct(self, request: AnalysisRequest) -> str:
        """Direct OpenAI call without template"""
        messages = [
            {
                "role": "system",
                "content": "You are an expert financial analyst specializing in day trading."
            },
            {
                "role": "user",
                "content": self._build_text_prompt(request)
            }
        ]
        
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.3
        )
        
        return response.choices[0].message.content
    
    def _build_text_prompt(self, request: AnalysisRequest) -> str:
        """Build analysis prompt"""
        prompt = f"""
        Analyze this {request.item_type} for {request.symbol}:
        
        Title: {request.title}
        Content: {request.text}
        """
        
        if request.technical:
            prompt += f"\n\nTechnical Analysis:\n{request.technical}"
        
        prompt += """
        
        Provide a JSON response with the exact structure:
        {
            "summary": "Brief trading strategy summary",
            "action": "buy",
            "confidence": 75,
            "event_time": null,
            "levels": {
                "entry": null,
                "take_profit": null,
                "stop_loss": null,
                "support": null,
                "resistance": null
            }
        }
        
        Important:
        - action must be exactly "buy", "sell", or "hold"
        - confidence must be a number between 0-100
        - event_time can be null or ISO-8601 date-time string
        - levels values can be null or numbers
        - Return ONLY the JSON, no markdown formatting or additional text
        """
        
        return prompt
    
    def _build_image_prompt(self, symbol: str) -> str:
        """Build image analysis prompt"""
        return f"""You are an expert day trader. Analyze the attached image, which contains a Technical Analysis chart for {symbol} to extract a day trading strategy.
Return a {symbol} trading brief with:
- Focus on expressing a day trading hypothesis/strategy for {symbol} with clear indication of (buy/sell/hold) action in ≤500 words.  
- Identify overall direction (trend lines, channels, patterns)
- Use OCR recognition if needed to understand notes
- Note key levels (Entry, Profit Taking, Stop-Loss, Support, Resistance)
- Determine if there's any imminent breakouts or trend reversals
- Infer timing: infer the most critical time to watch out for
- Do not fabricate any information.
- Express full numeric values eg. 97k -> 97,000 USD
- Ensure especially the currency/price levels and timing information is consistent and accurate
- Go straight to the point and use a formal tone without filler words.
- If the image is not a chart or technical analysis, return "No chart found".
- If the technical analysis in the image is not clear or poorly executed, shorten the analysis and add a note that it is not clear or poorly executed."""
    
    def _parse_response(self, response: str) -> AnalysisResult:
        """Parse JSON response to AnalysisResult"""
        try:
            # Clean the response - remove markdown formatting and extract JSON
            cleaned_response = self._extract_json_from_response(response)
            data = json.loads(cleaned_response)
            
            # Parse action
            action_str = data.get('action', 'hold').lower()
            try:
                action = AnalysisAction(action_str.upper())
            except ValueError:
                action = AnalysisAction.HOLD
            
            # Parse confidence (0-100 to 0-1)
            confidence = data.get('confidence', 50) / 100.0
            
            # Parse levels
            levels = data.get('levels', {})
            if levels and isinstance(levels, dict):
                # Ensure all required level fields exist
                for key in ['entry', 'take_profit', 'stop_loss', 'support', 'resistance']:
                    if key not in levels:
                        levels[key] = None
            
            return AnalysisResult(
                summary=data.get('summary', ''),
                action=action,
                confidence=confidence,
                event_time=data.get('event_time'),
                levels=levels
            )
            
        except json.JSONDecodeError as e:
            # Fallback for non-JSON response
            debug_warning(f"Failed to parse JSON response: {e}, using fallback")
            return AnalysisResult(
                summary=response[:500] if len(response) > 500 else response,
                action=AnalysisAction.HOLD,
                confidence=0.5
            )
    
    def _extract_json_from_response(self, response: str) -> str:
        """Extract JSON from response that may contain markdown or other formatting"""
        # Remove markdown code blocks
        if '```json' in response:
            start = response.find('```json') + 7
            end = response.find('```', start)
            if end != -1:
                return response[start:end].strip()
        
        # Remove markdown code blocks without language
        if '```' in response:
            start = response.find('```') + 3
            end = response.find('```', start)
            if end != -1:
                return response[start:end].strip()
        
        # Look for JSON object boundaries
        start = response.find('{')
        if start != -1:
            # Find matching closing brace
            brace_count = 0
            for i, char in enumerate(response[start:], start):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        return response[start:i+1]
        
        # If no JSON found, return original response
        return response
    
    async def analyze_text_async(self, request: AnalysisRequest) -> AnalysisResult:
        """
         ┌─────────────────────────────────────┐
         │      ANALYZE_TEXT_ASYNC             │
         └─────────────────────────────────────┘
         Async analyze text using OpenAI
         
         Non-blocking version for use in async contexts.
        """
        # Apply rate limiting (async)
        await self.rate_limiter.wait_if_needed()
        
        try:
            # Add timeout to prevent hanging
            try:
                timeout_seconds = OPENAI_TIMEOUT / 1000.0  # Convert milliseconds to seconds
                if OPENAI_PROMPT_BRIEFSTRATEGY_ID and OPENAI_PROMPT_BRIEFSTRATEGY_VERSION_ID:
                    response = await asyncio.wait_for(self._call_with_template_async(request), timeout=timeout_seconds)
                else:
                    response = await asyncio.wait_for(self._call_direct_async(request), timeout=timeout_seconds)
            except asyncio.TimeoutError:
                debug_error(f"OpenAI text analysis timed out after {OPENAI_TIMEOUT}ms")
                raise Exception("OpenAI API request timed out")
            
            # Parse response
            result = self._parse_response(response)
            return result
            
        except Exception as e:
            raise
    
    async def analyze_image_async(self, request: ImageAnalysisRequest) -> str:
        """
         ┌─────────────────────────────────────┐
         │     ANALYZE_IMAGE_ASYNC             │
         └─────────────────────────────────────┘
         Async analyze image using OpenAI Vision
         
         Non-blocking version for use in async contexts.
        """
        # Apply rate limiting (async)
        await self.rate_limiter.wait_if_needed()
        
        try:
            prompt = self._build_image_prompt(request.symbol)
            
            # Add timeout to prevent hanging
            try:
                timeout_seconds = OPENAI_TIMEOUT / 1000.0  # Convert milliseconds to seconds
                response = await asyncio.wait_for(
                    self.async_client.chat.completions.create(
                    model=OPENAI_MODEL,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert day trader and technical analyst."
                        },
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {"type": "image_url", "image_url": {"url": request.image_url}}
                            ]
                        }
                    ]
                ), timeout=timeout_seconds)
            except asyncio.TimeoutError:
                debug_error(f"OpenAI image analysis timed out after {OPENAI_TIMEOUT}ms")
                raise Exception("OpenAI API request timed out")
            
            analysis = response.choices[0].message.content
            debug_info(f"Image analysis completed ({len(analysis)} chars)")
            
            return analysis
            
        except Exception as e:
            raise
    
    async def _call_with_template_async(self, request: AnalysisRequest) -> str:
        """Async call OpenAI using prompt template"""
        prompt = {
            "id": OPENAI_PROMPT_BRIEFSTRATEGY_ID,
            "version": OPENAI_PROMPT_BRIEFSTRATEGY_VERSION_ID,
            "variables": {
                "symbol": request.symbol,
                "item_type": request.item_type,
                "title": request.title,
                "content": request.text,
                "technical_analysis": request.technical
            }
        }
        
        # Note: If using prompt templates, adjust this to use the appropriate async method
        # For now, falling back to direct call
        return await self._call_direct_async(request)
    
    async def _call_direct_async(self, request: AnalysisRequest) -> str:
        """Async direct OpenAI call without template"""
        messages = [
            {
                "role": "system",
                "content": "You are an expert financial analyst specializing in day trading."
            },
            {
                "role": "user",
                "content": self._build_text_prompt(request)
            }
        ]
        
        response = await self.async_client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.3
        )
        
        return response.choices[0].message.content
    
    def analyze_report(self, request: AnalysisRequest) -> AnalysisResult:
        """
         ┌─────────────────────────────────────┐
         │        ANALYZE_REPORT               │
         └─────────────────────────────────────┘
         Generate AI report using OpenAI
         
         Uses the report-specific prompt template for comprehensive
         analysis of multiple insights.
        """
        debug_info(f"OpenAI Report Analysis for {request.symbol}")
        
        try:
            # Use report prompt template if configured
            if OPENAI_PROMPT_REPORT_ID and OPENAI_PROMPT_REPORT_VERSION_ID:
                response = self._call_with_report_template(request)
            else:
                # Fallback to direct call with report-specific prompt
                response = self._call_direct_report(request)
            
            # Parse response
            result = self._parse_response(response)
            return result
            
        except Exception as e:
            debug_error(f"Report analysis failed: {e}")
            raise
    
    def _call_with_report_template(self, request: AnalysisRequest) -> str:
        """Call OpenAI with report template"""
        # Apply rate limiting (sync version)
        time.sleep(self.rate_limiter.get_wait_time())
        
        # Prepare the API call with report template
        messages = [
            {
                "role": "system",
                "content": f"You are an expert financial analyst. Generate a comprehensive trading report."
            },
            {
                "role": "user", 
                "content": self._build_report_prompt(request)
            }
        ]
        
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.3
        )
        
        return response.choices[0].message.content
    
    def _call_direct_report(self, request: AnalysisRequest) -> str:
        """Direct call without template for report generation"""
        # Apply rate limiting (sync version)
        time.sleep(self.rate_limiter.get_wait_time())
        
        messages = [
            {
                "role": "system",
                "content": "You are an expert financial analyst. Generate a comprehensive trading report."
            },
            {
                "role": "user",
                "content": self._build_report_prompt(request)
            }
        ]
        
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.3
        )
        
        return response.choices[0].message.content
    
    def _build_report_prompt(self, request: AnalysisRequest) -> str:
        """Build report analysis prompt"""
        prompt = f"""
        Generate a comprehensive trading report for {request.symbol} based on the following insights:
        
        {request.text}
        
        Provide a JSON response with the exact structure:
        {{
            "summary": "Comprehensive trading analysis and recommendation",
            "action": "buy",
            "confidence": 75,
            "event_time": null,
            "levels": {{
                "entry": null,
                "take_profit": null,
                "stop_loss": null,
                "support": null,
                "resistance": null
            }}
        }}
        
        Important:
        - action must be exactly "buy", "sell", or "hold"
        - confidence must be a number between 0-100
        - event_time can be null or ISO-8601 date-time string
        - levels values can be null or numbers
        - Return ONLY the JSON, no markdown formatting or additional text
        """
        
        return prompt



