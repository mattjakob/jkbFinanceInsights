"""
┌─────────────────────────────────────┐
│            DEBUGGER                 │
└─────────────────────────────────────┘

Simple debugger system for console and frontend message display.

This module provides a unified debugging interface that outputs messages
to both the Uvicorn console and sends them to the frontend status bar
for real-time user feedback.
"""

import logging
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
import json

# Configure logging for Uvicorn console output
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

class Debugger:
    """
     ┌─────────────────────────────────────┐
     │            DEBUGGER                 │
     └─────────────────────────────────────┘
     Unified debugging system for console and frontend messaging
     
     Provides methods to send debug messages both to the server console
     and to the frontend status bar for real-time user feedback.
    """
    
    def __init__(self):
        self.current_message = ""
        self.current_status = "info"
        self.timestamp = None
    
    def debug(self, message: str, status: str = "info") -> None:
        """
         ┌─────────────────────────────────────┐
         │             DEBUG                   │
         └─────────────────────────────────────┘
         Send debug message to console and store for frontend
         
         Outputs the message to the Uvicorn console using the logging system
         and stores it for frontend retrieval via the status API.
         
         Parameters:
         - message: Debug message to display
         - status: Status level (info, warning, error, success)
         
         Returns:
         - None
         
         Notes:
         - Messages are logged to console immediately
         - Messages are stored for frontend status bar updates
        """
        # Update internal state
        self.current_message = message
        self.current_status = status
        self.timestamp = datetime.now()
        
        # Send to console based on status level
        if status == "error":
            logger.error(message)
        elif status == "warning":
            logger.warning(message)
        elif status == "success":
            logger.info(f"✓ {message}")
        else:  # info
            logger.info(message)
    
    def get_current_status(self) -> Dict[str, Any]:
        """
         ┌─────────────────────────────────────┐
         │        GET_CURRENT_STATUS           │
         └─────────────────────────────────────┘
         Get current debug status for frontend
         
         Returns the current debug message and status for display
         in the frontend status bar.
         
         Returns:
         - Dictionary with message, status, and timestamp
        """
        return {
            "message": self.current_message,
            "status": self.current_status,
            "timestamp": self.timestamp,
        }
    
    def clear(self) -> None:
        """
         ┌─────────────────────────────────────┐
         │             CLEAR                   │
         └─────────────────────────────────────┘
         Clear current debug message
         
         Resets the current message state.
        """
        self.current_message = ""
        self.current_status = "info"
        self.timestamp = None

# Global debugger instance
debugger = Debugger()

# Convenience functions for different status levels
def debug_info(message: str) -> None:
    """Send an info debug message"""
    debugger.debug(message, "info")

def debug_warning(message: str) -> None:
    """Send a warning debug message"""
    debugger.debug(message, "warning")

def debug_error(message: str) -> None:
    """Send an error debug message"""
    debugger.debug(message, "error")

def debug_success(message: str) -> None:
    """Send a success debug message"""
    debugger.debug(message, "success")
