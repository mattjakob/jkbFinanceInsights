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
        self.message_history = []  # Store recent messages
        self.max_history = 50  # Keep last 50 messages in backend
    
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
        # Update internal state only if we have a valid message
        if message and message.strip():
            self.current_message = message
            self.current_status = status
            self.timestamp = datetime.now()
        
        # Add to message history
        self.message_history.append({
            'message': message,
            'status': status,
            'timestamp': self.timestamp.isoformat()
        })
        
        # Keep only recent messages
        if len(self.message_history) > self.max_history:
            self.message_history = self.message_history[-self.max_history:]
        
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
        # If current message is empty but we have history, use the last message
        message = self.current_message
        status = self.current_status
        timestamp = self.timestamp
        
        if not message and self.message_history:
            last_message = self.message_history[-1]
            message = last_message['message']
            status = last_message['status']
            timestamp = datetime.fromisoformat(last_message['timestamp'])
        
        return {
            "message": message,
            "status": status,
            "timestamp": timestamp.isoformat() if timestamp else None,
            "history": self.message_history[-10:]  # Send last 10 messages to UI
        }
    


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
