"""
/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │         MAIN ENTRY POINT            │
 *  └─────────────────────────────────────┘
 *  Application entry point for JKB Finance Insights
 * 
 *  Simple entry point that imports the app from the app factory
 *  and runs it with uvicorn when executed directly.
 * 
 *  Parameters:
 *  - None
 * 
 *  Returns:
 *  - None (runs server)
 * 
 *  Notes:
 *  - Uses app factory pattern for better organization
 *  - All application logic is in app.py
 */
"""

import uvicorn
from app import app
from debugger import debug_success
from config import SERVER_HOST, SERVER_PORT

if __name__ == "__main__":
    debug_success("Starting Finance Insights server...")
    uvicorn.run(
        "app:app",
        host=SERVER_HOST,
        port=SERVER_PORT,
        reload=True,
        log_level="info"
    )
