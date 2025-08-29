# Environment Configuration Update

## Changes Made

### 1. Restored Important OpenAI Settings
- Added back `OPENAI_PROMPT_BRIEFSTRATEGY_ID`
- Added back `OPENAI_PROMPT_BRIEFSTRATEGY_VERSION_ID`
- These are now properly validated at startup

### 2. Improved Organization (Semantic Grouping)

The env.example file is now organized into clear semantic sections:

1. **SERVER CONFIGURATION**
   - SERVER_HOST
   - SERVER_PORT

2. **DATABASE CONFIGURATION**
   - DATABASE_URL

3. **OPENAI CONFIGURATION**
   - OPENAI_API_KEY
   - OPENAI_MODEL
   - OPENAI_PROMPT_BRIEFSTRATEGY_ID
   - OPENAI_PROMPT_BRIEFSTRATEGY_VERSION_ID

4. **UI/FRONTEND CONFIGURATION**
   - Feature toggles (auto_refresh, ai_analysis, etc.)
   - Performance settings (refresh interval, timeout)

5. **WORKER/TASK CONFIGURATION**
   - PERFORMANCE_WORKER_COUNT
   - TASK_MAX_RETRIES
   - TASK_CLEANUP_DAYS

6. **SCRAPER CONFIGURATION**
   - SCRAPER_TIMEOUT
   - SCRAPER_MAX_RETRIES
   - SCRAPER_RETRY_DELAY

7. **AI ANALYSIS CONFIGURATION**
   - AI_CIRCUIT_BREAKER_THRESHOLD
   - AI_CIRCUIT_BREAKER_RESET_MINUTES

8. **SECURITY CONFIGURATION**
   - RATE_LIMIT_REQUESTS_PER_MINUTE
   - CORS settings

9. **DEVELOPMENT CONFIGURATION**
   - SHOW_DETAILED_ERRORS
   - LOG_LEVEL

10. **TRADINGVIEW CONFIGURATION**
    - Chart settings

11. **APPLICATION INFO**
    - APP_NAME

### 3. Enhanced Validation

The config.py now properly validates all AI-related settings:
- Checks for OPENAI_API_KEY
- Checks for OPENAI_PROMPT_BRIEFSTRATEGY_ID
- Checks for OPENAI_PROMPT_BRIEFSTRATEGY_VERSION_ID
- Disables AI features if any are missing
- Provides clear warning messages

### 4. All Settings Now Configurable

Every setting that was hardcoded is now configurable via environment variables:
- TradingView settings
- AI circuit breaker settings
- Task cleanup days
- All scraper settings

## Total Configuration Count

While the simplified approach reduced many redundant settings, we maintain all necessary configurations:
- **Core Required**: 6 settings (including OpenAI prompt IDs)
- **Optional with Smart Defaults**: ~25 settings
- **Total**: ~31 settings (down from 60+)

The key improvement is that most settings have sensible defaults and are logically grouped, making it much easier to understand and configure only what you need to change.
