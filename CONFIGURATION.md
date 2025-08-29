# Configuration Guide

## Overview

The JKB Finance Insights application now uses a comprehensive environment-based configuration system that eliminates hardcoded values and provides centralized control over all application settings.

## Quick Start

1. **Copy the example environment file:**
   ```bash
   cp env.example .env
   ```

2. **Edit the `.env` file** with your desired settings
3. **Restart the application** to load the new configuration

## Configuration Categories

### Server Configuration
- `SERVER_HOST`: Server host address (default: 127.0.0.1)
- `SERVER_PORT`: Server port (default: 8000)

### Database Configuration
- `DATABASE_URL`: SQLite database file path (default: finance_insights.db)

### Scraper Configuration
- `SCRAPER_TIMEOUT`: Request timeout in seconds (default: 30)
- `SCRAPER_MAX_RETRIES`: Maximum retry attempts (default: 3)
- `SCRAPER_RETRY_DELAY`: Delay between retries in seconds (default: 1)

### AI Configuration
- `OPENAI_API_KEY`: Your OpenAI API key (required for AI analysis)
- `OPENAI_MODEL`: AI model to use (default: gpt-4-vision-preview)
- `AI_CIRCUIT_BREAKER_THRESHOLD`: Circuit breaker threshold (default: 3)
- `AI_CIRCUIT_BREAKER_RESET_MINUTES`: Reset timeout in minutes (default: 60)

### Task Queue Configuration
- `TASK_WORKER_COUNT`: Number of worker processes (default: 3)
- `TASK_MAX_RETRIES`: Maximum task retry attempts (default: 3)
- `TASK_CLEANUP_DAYS`: Days to keep completed tasks (default: 7)

### Frontend Refresh Intervals (milliseconds)
- `FRONTEND_AGE_REFRESH_INTERVAL`: Age display updates (default: 1000)
- `FRONTEND_AUTO_REFRESH_INTERVAL`: Main data refresh (default: 6000)
- `FRONTEND_TASK_UPDATE_INTERVAL`: Task status updates (default: 5000)
- `FRONTEND_STATUS_UPDATE_INTERVAL`: Status bar updates (default: 1000)
- `FRONTEND_DEBUGGER_FETCH_INTERVAL`: Debugger updates (default: 5000)

### Application Behavior Settings
- `APP_RELOAD_DELAY`: Page reload delay after operations (default: 1000)
- `APP_DEFAULT_MAX_ITEMS`: Default items to fetch (default: 10)
- `APP_SYMBOL_SEARCH_DEBOUNCE`: Symbol search debounce (default: 200)
- `APP_SYMBOL_FILTER_DELAY`: Symbol filter update delay (default: 800)

### TradingView Chart Configuration
- `TRADINGVIEW_CHART_HEIGHT`: Chart height in pixels (default: 400)
- `TRADINGVIEW_CHART_INTERVAL`: Chart update interval (default: 1)
- `TRADINGVIEW_CHART_TIMEZONE`: Chart timezone (default: America/New_York)

### Debug and Logging
- `DEBUG_MODE`: Enable debug mode (default: false)
- `LOG_LEVEL`: Application log level (default: info)
- `DEBUGGER_ENABLED`: Enable debugger interface (default: true)

### Security and Rate Limiting
- `RATE_LIMIT_REQUESTS_PER_MINUTE`: Rate limit per IP (default: 100)
- `CORS_ENABLED`: Enable CORS (default: true)
- `CORS_ALLOWED_ORIGINS`: Allowed CORS origins (comma-separated)

### Development Settings
- `DEV_MODE`: Enable development features (default: true)
- `FRONTEND_HOT_RELOAD`: Enable frontend hot reload (default: true)
- `SHOW_DETAILED_ERRORS`: Show detailed error messages (default: true)

## Environment Variable Format

All boolean values use `true`/`false` strings that are converted to Python booleans.

All numeric values are automatically converted to the appropriate Python type.

## Frontend Configuration

The frontend JavaScript components now automatically use the configuration values passed from the backend:

```javascript
// Access global configuration
const config = window.AppConfig;

// Use configuration values with fallbacks
const updateInterval = window.AppConfig?.frontend_status_update_interval || 1000;
```

## Configuration Validation

The application validates configuration values on startup and provides clear error messages for invalid settings.

## Production vs Development

### Development (.env)
```bash
DEBUG_MODE=true
DEV_MODE=true
UVICORN_RELOAD=true
FRONTEND_HOT_RELOAD=true
```

### Production (.env)
```bash
DEBUG_MODE=false
DEV_MODE=false
UVICORN_RELOAD=false
FRONTEND_HOT_RELOAD=false
```

## Configuration Updates

After changing `.env` values:
1. Save the file
2. Restart the application
3. The new values will be loaded automatically

## Troubleshooting

### Common Issues

1. **Configuration not loaded**: Ensure `.env` file is in the project root
2. **Invalid values**: Check the console for configuration validation errors
3. **Frontend not updated**: Clear browser cache and refresh

### Debug Configuration

To see current configuration values:
```bash
curl http://localhost:8000/api/debug-status
```

## Best Practices

1. **Never commit `.env` files** to version control
2. **Use descriptive names** for custom configuration
3. **Provide sensible defaults** for all configuration options
4. **Document configuration changes** in commit messages
5. **Test configuration** in development before production

## Migration from Hardcoded Values

All previously hardcoded values have been moved to configuration:

- ✅ Refresh intervals
- ✅ Timeout values
- ✅ Retry counts
- ✅ Chart settings
- ✅ UI behavior settings
- ✅ Development flags

## Configuration Inheritance

The system uses a fallback hierarchy:
1. Environment variable value
2. Default value from config.py
3. Hardcoded fallback in JavaScript

This ensures the application always has valid configuration values.
