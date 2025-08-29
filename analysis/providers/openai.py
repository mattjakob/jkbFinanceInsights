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

import time
from openai import OpenAI

from .base import AIProvider
from ..models import AnalysisRequest, ImageAnalysisRequest, AnalysisResult, AnalysisAction
from config import (
    OPENAI_API_KEY, OPENAI_MODEL,
    OPENAI_PROMPT_BRIEFSTRATEGY_ID, OPENAI_PROMPT_BRIEFSTRATEGY_VERSION_ID,
    AI_CIRCUIT_BREAKER_THRESHOLD, AI_CIRCUIT_BREAKER_RESET_MINUTES
)
from debugger import debug_info, debug_error, debug_warning, debug_success


class RateLimiter:
    """Simple rate limiter to prevent API overload"""
    
    def __init__(self, max_calls_per_minute: int = 10):
        self.max_calls_per_minute = max_calls_per_minute
        self.calls = []
        self.min_delay_between_calls = 1.0  # Minimum 1 second between calls
        self.last_call_time = 0
    
    def wait_if_needed(self):
        """Wait if we're hitting rate limits"""
        now = time.time()
        
        # Ensure minimum delay between calls
        time_since_last_call = now - self.last_call_time
        if time_since_last_call < self.min_delay_between_calls:
            delay = self.min_delay_between_calls - time_since_last_call
            debug_info(f"Rate limiter: waiting {delay:.2f}s before next call")
            time.sleep(delay)
            now = time.time()
        
        # Remove calls older than 1 minute
        self.calls = [call_time for call_time in self.calls if now - call_time < 60]
        
        # If we've hit the limit, wait
        if len(self.calls) >= self.max_calls_per_minute:
            wait_time = 60 - (now - self.calls[0]) + 1
            debug_warning(f"Rate limit reached ({self.max_calls_per_minute} calls/min), waiting {wait_time:.2f}s")
            time.sleep(wait_time)
            # Clean up old calls after waiting
            now = time.time()
            self.calls = [call_time for call_time in self.calls if now - call_time < 60]
        
        # Record this call
        self.calls.append(now)
        self.last_call_time = now


class CircuitBreaker:
    """Simple circuit breaker for API quota management"""
    
    def __init__(self, threshold: int = 3, reset_minutes: int = 60):
        self.threshold = threshold
        self.reset_minutes = reset_minutes
        self.is_open = False
        self.consecutive_errors = 0
        self.last_error_time: Optional[datetime] = None
    
    def is_available(self) -> bool:
        """Check if circuit is closed (API available)"""
        if not self.is_open:
            return True
        
        # Check if reset time has passed
        if self.last_error_time:
            reset_time = self.last_error_time + timedelta(minutes=self.reset_minutes)
            if datetime.now() > reset_time:
                self.reset()
                return True
        
        return False
    
    def record_success(self):
        """Record successful API call"""
        if self.consecutive_errors > 0:
            debug_info("OpenAI API call successful - resetting error counter")
            self.consecutive_errors = 0
    
    def record_error(self):
        """Record API error"""
        self.consecutive_errors += 1
        self.last_error_time = datetime.now()
        
        if self.consecutive_errors >= self.threshold:
            self.is_open = True
            debug_error(f"OpenAI circuit breaker OPENED after {self.consecutive_errors} errors")
            debug_info(f"Will retry after {self.reset_minutes} minutes")
    
    def reset(self):
        """Reset circuit breaker"""
        self.is_open = False
        self.consecutive_errors = 0
        self.last_error_time = None
        debug_info("OpenAI circuit breaker reset")


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
        
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.circuit_breaker = CircuitBreaker(
            threshold=AI_CIRCUIT_BREAKER_THRESHOLD,
            reset_minutes=AI_CIRCUIT_BREAKER_RESET_MINUTES
        )
        # Add rate limiter - 10 calls per minute to stay well under OpenAI limits
        self.rate_limiter = RateLimiter(max_calls_per_minute=10)
    
    def analyze_text(self, request: AnalysisRequest) -> AnalysisResult:
        """
         ┌─────────────────────────────────────┐
         │        ANALYZE_TEXT                 │
         └─────────────────────────────────────┘
         Analyze text using OpenAI
         
         Uses the configured prompt template for structured
         financial analysis.
        """
        # Check circuit breaker
        if not self.circuit_breaker.is_available():
            raise Exception("OpenAI API temporarily unavailable (circuit breaker open)")
        
        # Apply rate limiting
        self.rate_limiter.wait_if_needed()
        
        try:
            # Use prompt template if configured
            if OPENAI_PROMPT_BRIEFSTRATEGY_ID and OPENAI_PROMPT_BRIEFSTRATEGY_VERSION_ID:
                response = self._call_with_template(request)
            else:
                response = self._call_direct(request)
            
            # Parse response
            result = self._parse_response(response)
            
            self.circuit_breaker.record_success()
            return result
            
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "quota" in error_msg.lower():
                self.circuit_breaker.record_error()
            raise
    
    def analyze_image(self, request: ImageAnalysisRequest) -> str:
        """
         ┌─────────────────────────────────────┐
         │       ANALYZE_IMAGE                 │
         └─────────────────────────────────────┘
         Analyze image using OpenAI Vision
         
         Extracts trading strategy from chart images.
        """
        # Check circuit breaker
        if not self.circuit_breaker.is_available():
            raise Exception("OpenAI API temporarily unavailable (circuit breaker open)")
        
        # Apply rate limiting
        self.rate_limiter.wait_if_needed()
        
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
            
            self.circuit_breaker.record_success()
            debug_info(f"Image analysis completed ({len(analysis)} chars)")
            
            return analysis
            
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "quota" in error_msg.lower():
                self.circuit_breaker.record_error()
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
        
        Provide a JSON response with:
        {
            "summary": "Brief trading strategy summary",
            "action": "buy|sell|hold",
            "confidence": 0-100,
            "event_time": "When to act",
            "levels": {
                "entry": number,
                "take_profit": number,
                "stop_loss": number,
                "support": [numbers],
                "resistance": number
            }
        }
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
            data = json.loads(response)
            
            # Parse action
            action_str = data.get('action', 'hold').upper()
            try:
                action = AnalysisAction(action_str)
            except ValueError:
                action = AnalysisAction.HOLD
            
            # Parse confidence (0-100 to 0-1)
            confidence = data.get('confidence', 50) / 100.0
            
            return AnalysisResult(
                summary=data.get('summary', ''),
                action=action,
                confidence=confidence,
                event_time=data.get('event_time'),
                levels=data.get('levels')
            )
            
        except json.JSONDecodeError:
            # Fallback for non-JSON response
            debug_warning("Failed to parse JSON response, using fallback")
            return AnalysisResult(
                summary=response[:500] if len(response) > 500 else response,
                action=AnalysisAction.HOLD,
                confidence=0.5
            )



