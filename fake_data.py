"""
 ┌─────────────────────────────────────┐
 │           FAKE DATA                 │
 └─────────────────────────────────────┘
 Generate fake financial data for testing
 
 Provides functions to create and update insights with realistic
 financial data for testing and demonstration purposes.
"""

import random
import items_management
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from debugger import debug_info, debug_warning, debug_error, debug_success

# Sample data pools
TITLES = [
    "Bitcoin Breaks Key Resistance Level at $45,000",
    "Fed Minutes Suggest Rate Hike Pause",
    "Tech Sector Shows Strong Recovery Signals",
    "Oil Prices Surge on Supply Concerns",
    "Gold Reaches 6-Month High Amid Dollar Weakness",
    "Nasdaq Futures Point to Positive Open",
    "Cryptocurrency Market Cap Exceeds $2 Trillion",
    "S&P 500 Tests All-Time High",
    "Emerging Markets Show Divergence",
    "Treasury Yields Fall on Growth Concerns",
    "Dollar Index Weakens Against Major Currencies",
    "Retail Sales Beat Expectations",
    "Housing Market Shows Signs of Cooling",
    "Energy Sector Leads Market Gains",
    "Banking Stocks Rally on Earnings",
]

CONTENT_TEMPLATES = [
    "Market analysis indicates {trend} momentum in {asset} with volume {volume}% above average. Technical indicators suggest {action} bias with key levels at {level1} and {level2}.",
    "Breaking: {asset} shows {trend} price action following {event}. Analysts predict {outlook} in the {timeframe} term with resistance at {level2}.",
    "Institutional investors are {action} {asset} as {reason}. Current market sentiment remains {sentiment} with support levels holding at {level1}.",
    "{asset} volatility increases as traders position for {event}. Options flow indicates {sentiment} bias with unusual activity in {timeframe} contracts.",
    "Technical analysis reveals {pattern} formation in {asset}. Breakout expected above {level2} with targets at {target}.",
]

SUMMARIES = [
    "Strong bullish momentum detected with increasing volume",
    "Bearish divergence forming, caution advised",
    "Consolidation phase with neutral bias",
    "Breakout imminent, watch key resistance levels",
    "Support holding firm, potential reversal setup",
    "Overbought conditions suggest pullback likely",
    "Oversold bounce expected from current levels",
    "Range-bound trading continues, await catalyst",
    "Trend reversal confirmed by multiple indicators",
    "Accumulation phase detected, bullish outlook",
]

ACTIONS = ["BUY", "SELL", "HOLD", "WATCH", "ANALYZE"]

ASSETS = ["BTC/USD", "ETH/USD", "S&P 500", "NASDAQ", "Gold", "Oil", "EUR/USD", "Tesla", "Apple", "Bitcoin"]
TRENDS = ["bullish", "bearish", "sideways", "volatile", "strong", "weak"]
SENTIMENTS = ["bullish", "bearish", "neutral", "mixed", "cautious", "optimistic"]
EVENTS = ["earnings report", "economic data", "Fed decision", "geopolitical tensions", "technical breakout"]
PATTERNS = ["ascending triangle", "head and shoulders", "double bottom", "flag", "wedge"]
TIMEFRAMES = ["short", "medium", "long", "near"]

def generate_random_content() -> str:
    """Generate random financial content using templates"""
    template = random.choice(CONTENT_TEMPLATES)
    
    # Calculate some semi-realistic levels
    base_price = random.uniform(100, 50000)
    level1 = round(base_price * 0.95, 2)
    level2 = round(base_price * 1.05, 2)
    target = round(base_price * 1.10, 2)
    
    content = template.format(
        asset=random.choice(ASSETS),
        trend=random.choice(TRENDS),
        volume=random.randint(20, 200),
        action=random.choice(["accumulating", "distributing", "monitoring"]),
        level1=f"${level1:,.2f}",
        level2=f"${level2:,.2f}",
        target=f"${target:,.2f}",
        event=random.choice(EVENTS),
        outlook=random.choice(["growth", "decline", "stability"]),
        timeframe=random.choice(TIMEFRAMES),
        reason=random.choice(["market conditions improve", "risk appetite returns", "technical setup develops"]),
        sentiment=random.choice(SENTIMENTS),
        pattern=random.choice(PATTERNS)
    )
    
    return content

def generate_levels() -> str:
    """Generate support and resistance levels"""
    base = random.uniform(1000, 50000)
    support = round(base * 0.95, 2)
    resistance = round(base * 1.05, 2)
    return f"S: {support:,.2f}, R: {resistance:,.2f}"

def generate_random_insight() -> Dict:
    """
     ┌─────────────────────────────────────┐
     │     GENERATE_RANDOM_INSIGHT         │
     └─────────────────────────────────────┘
     Generate a complete random insight
     
     Creates a realistic financial insight with all fields populated.
     
     Returns:
     - Dictionary with insight data
    """
    # Get feed names
    feed_names = items_management.get_feed_names()
    if not feed_names:
        raise ValueError("No feed names available in database")
    
    # Generate time posted (random time in last 24 hours)
    hours_ago = random.randint(0, 24)
    time_posted = (datetime.now() - timedelta(hours=hours_ago)).isoformat()
    
    # Generate AI event time (sometime in next 24 hours)
    hours_ahead = random.randint(1, 24)
    ai_event_time = (datetime.now() + timedelta(hours=hours_ahead)).isoformat()
    
    # Generate symbol and exchange
    symbol = random.choice(["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN", "NVDA", "META", "NFLX", "BTC", "ETH"])
    exchange = random.choice(["NASDAQ", "NYSE", "CRYPTO", "FOREX", "COMMODITIES"])
    
    insight_data = {
        'type': random.choice(feed_names)['name'],
        'title': random.choice(TITLES),
        'content': generate_random_content(),
        'timePosted': time_posted,
        'symbol': symbol,
        'exchange': exchange,
        'imageURL': f"https://example.com/chart_{random.randint(1000, 9999)}.png" if random.random() > 0.5 else None,

        'AIImageSummary': "Chart shows " + random.choice(["bullish flag", "bearish wedge", "consolidation", "breakout"]) if random.random() > 0.3 else None,
        'AISummary': random.choice(SUMMARIES),
        'AIAction': random.choice(ACTIONS),
        'AIConfidence': round(random.uniform(0.65, 0.95), 2),
        'AIEventTime': ai_event_time,
        'AILevels': generate_levels()
    }
    
    return insight_data

def add_random_insights(count: int = 5) -> List[int]:
    """
     ┌─────────────────────────────────────┐
     │       ADD_RANDOM_INSIGHTS           │
     └─────────────────────────────────────┘
     Add multiple random insights to database
     
     Parameters:
     - count: Number of insights to add
     
     Returns:
     - List of created insight IDs
    """
    created_ids = []
    
    for _ in range(count):
        insight_data = generate_random_insight()
        try:
            insight_id = items_management.add_insight(**insight_data)
            created_ids.append(insight_id)
            debug_success(f"Created insight #{insight_id}: {insight_data['title']}")
        except Exception as e:
            debug_error(f"Error creating insight: {e}")
    
    return created_ids

def fake_do_ai_analysis() -> int:
    """
     ┌─────────────────────────────────────┐
     │    UPDATE_INSIGHTS_WITH_AI_DATA     │
     └─────────────────────────────────────┘
     Update existing insights that lack AI data
     
     Finds insights with empty AISummary and chooses a random subset
     to update with fake AI data.
     
     Returns:
     - Number of insights updated
    """
    # Get insights without AI data (empty AISummary)
    insights = items_management.get_insights_for_ai()
    
    if not insights:
        debug_info("No insights need AI data - all insights already have AISummary")
        return 0
    
    debug_info(f"Found {len(insights)} insights with empty AISummary")
    
    # Choose a random subset (3-5 insights, or all if fewer than 3)
    num_to_update = min(random.randint(3, 5), len(insights))
    selected_insights = random.sample(insights, num_to_update)
    
    debug_info(f"Selected {num_to_update} insights to update with AI data")
    
    updated_count = 0
    
    for insight in selected_insights:
        # Generate fake AI data for all AI fields
        ai_data = {
            'AISummary': random.choice(SUMMARIES),
            'AIAction': random.choice(ACTIONS),
            'AIConfidence': round(random.uniform(0.65, 0.95), 2),
            'AILevels': generate_levels()
        }
        
        # Update the insight with AI data
        success = items_management.update_insight_ai_fields(insight['id'], **ai_data)
        if success:
            updated_count += 1
            debug_success(f"Updated insight #{insight['id']} ({insight['title'][:30]}...) with AI data")
    
    debug_success(f"Successfully updated {updated_count} insights with AI data")
    return updated_count

def populate_database_with_sample_data() -> None:
    """
     ┌─────────────────────────────────────┐
     │    POPULATE_DATABASE_WITH_SAMPLE_DATA │
     └─────────────────────────────────────┘
     Populate database with initial sample data
     
     Creates a set of diverse insights for testing if the
     database is empty or has very few entries.
    """
    current_insights = items_management.get_all_insights()
    
    if len(current_insights) < 10:
        debug_info("Database has few entries, adding initial sample data...")
        add_random_insights(10 - len(current_insights))
    else:
        debug_info(f"Database already has {len(current_insights)} insights")

# Test functions
if __name__ == "__main__":
    debug_info("Testing fake data generation...")
    
    # Add some random insights
    debug_info("1. Adding random insights:")
    created_ids = add_random_insights(3)
    
    # Update insights with AI data
    debug_info("2. Updating insights with AI data:")
    updated = fake_do_ai_analysis()
    
    
    # Populate database with sample data
    debug_info("4. Populating database with sample data:")
    populate_database_with_sample_data()
