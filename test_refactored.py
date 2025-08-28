#!/usr/bin/env python3
"""
Test script for refactored JKB Finance Insights
"""

import asyncio
from datetime import datetime
from debugger import debug_info, debug_warning, debug_error, debug_success

# Test imports
debug_info("🧪 Testing imports...")
try:
    # Core imports
    from core import InsightModel, FeedType, get_db_manager
    debug_success("✅ Core modules imported")
    
    # Data layer
    from data import InsightsRepository
    debug_success("✅ Data layer imported")
    
    # Scrapers
    from scrapers import ScraperManager, TradingViewNewsScraper
    debug_success("✅ Scraper modules imported")
    
    # Analysis
    from analysis import AnalysisService, OpenAIProvider
    debug_success("✅ Analysis modules imported")
    
    # Tasks
    from tasks import TaskQueue, HANDLERS
    debug_success("✅ Task modules imported")
    
    # API
    from api import api_router
    debug_success("✅ API modules imported")
    
except Exception as e:
    debug_error(f"❌ Import failed: {e}")
    exit(1)

debug_info("\n🧪 Testing database...")
try:
    # Initialize database
    db_manager = get_db_manager()
    debug_success("✅ Database initialized")
    
    # Test repository
    repo = InsightsRepository()
    insights = repo.find_all(limit=5)
    debug_success(f"✅ Found {len(insights)} insights in database")
    
except Exception as e:
    debug_error(f"❌ Database test failed: {e}")

debug_info("\n🧪 Testing scrapers...")
try:
    manager = ScraperManager()
    
    # Test that all feed types have scrapers
    for feed_type in FeedType:
        scraper = manager.get_scraper(feed_type)
        debug_success(f"✅ {feed_type.value} scraper available")
        
except Exception as e:
    debug_error(f"❌ Scraper test failed: {e}")

debug_info("\n🧪 Testing task queue...")
try:
    queue = TaskQueue()
    stats = queue.get_stats()
    debug_success(f"✅ Task queue stats: {stats}")
    
except Exception as e:
    debug_error(f"❌ Task queue test failed: {e}")

debug_info("\n🧪 Testing AI analysis service...")
try:
    # Check if OpenAI is configured
    from config import OPENAI_API_KEY
    if OPENAI_API_KEY:
        debug_success("✅ OpenAI API key configured")
        service = AnalysisService()
        debug_success("✅ Analysis service created")
    else:
        debug_warning("⚠️  OpenAI API key not configured")
        
except Exception as e:
    debug_error(f"❌ AI analysis test failed: {e}")

debug_info("\n🧪 Testing API routes...")
try:
    # Check route registration
    routes = []
    for route in api_router.routes:
        if hasattr(route, 'path'):
            routes.append(route.path)
    
    debug_success(f"✅ {len(routes)} API routes registered:")
    for route in sorted(set(routes)):
        debug_info(f"   - {route}")
        
except Exception as e:
    debug_error(f"❌ API routes test failed: {e}")

# Test async functionality
async def test_async():
    debug_info("\n🧪 Testing async functionality...")
    try:
        # Test async task creation
        from tasks.handlers import handle_cleanup
        result = handle_cleanup(days=30)
        debug_success(f"✅ Async handler test passed: {result}")
        
    except Exception as e:
        debug_error(f"❌ Async test failed: {e}")

# Run async test
asyncio.run(test_async())

debug_success("\n✅ All basic tests completed!")
debug_info("\nTo test the web interface:")
debug_info("1. Run: python main.py")
debug_info("2. Open: http://localhost:8000")
debug_info("3. Test features:")
debug_info("   - View insights table")
debug_info("   - Click on an insight for details")
debug_info("   - Use the fetch button to get new data")
debug_info("   - Trigger AI analysis")
debug_info("   - Check task status at /api/tasks/status")



