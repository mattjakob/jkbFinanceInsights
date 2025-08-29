#!/usr/bin/env python3
"""
Test the text report endpoint with sample data
"""

import requests
from datetime import datetime
from core.models import InsightModel, FeedType, AIAction, AIAnalysisStatus
from data.repositories.insights import InsightsRepository
from debugger import debug_info

# Create test insights with AI analysis
insights_repo = InsightsRepository()

# Create a test insight with full AI analysis
test_insight = {
    'type': FeedType.TD_NEWS,
    'symbol': 'TESTCOIN',
    'title': 'Test Insight with AI Analysis',
    'url': 'https://example.com/test',
    'time_posted': datetime.now(),
    'ai_summary': 'Strong bullish momentum detected. The asset has broken through key resistance levels with high volume, suggesting continued upward movement. Technical indicators show oversold conditions may be relieved.',
    'ai_action': AIAction.BUY,
    'ai_confidence': 0.85,
    'ai_event_time': '2025-01-15',
    'ai_levels': 'E: 45.50 | TP: 52.00 | SL: 42.00 | S: 41.00, 38.50 | R: 48.00, 50.00',
    'ai_analysis_status': AIAnalysisStatus.COMPLETED
}

# Create the insight
insight_id = insights_repo.create(test_insight)
debug_info(f"Created test insight with ID: {insight_id}")

# Test the text report endpoint
response = requests.get('http://localhost:8000/api/summaries/TESTCOIN')
print("\nText Report Response:")
print("=" * 60)
print(response.text)

# Clean up
insights_repo.delete(insight_id)
debug_info(f"Deleted test insight {insight_id}")
