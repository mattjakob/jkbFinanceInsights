/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │          CONFIGURATION              │
 *  └─────────────────────────────────────┘
 *  Central configuration for frontend application
 * 
 *  Contains all constants, settings, and configuration values
 *  used throughout the application.
 * 
 *  Parameters:
 *  - None
 * 
 *  Returns:
 *  - Configuration object
 * 
 *  Notes:
 *  - Update these values to change application behavior
 *  - Keep all magic numbers and strings here
 */

export const config = {
    // API endpoints
    api: {
        insights: '/api/insights',
        analysis: '/api/analysis',
        scraping: '/api/scraping',
        tasks: '/api/tasks',
        debug: '/api/debug-status',
        symbols: {
            search: '/api/symbols/search',
            validate: '/api/symbols/validate'
        }
    },
    
    // UI refresh intervals (in milliseconds) - use global config if available
    refreshIntervals: {
        age: window.AppConfig?.frontend_age_refresh_interval || 1000,
        table: window.AppConfig?.frontend_table_refresh_interval || 10000,
        status: window.AppConfig?.frontend_status_refresh_interval || 2000
    },
    
    // Default values - use global config if available
    defaults: {
        maxItems: window.AppConfig?.app_max_items || 25,
        reloadDelay: window.AppConfig?.app_reload_delay || 1000,
        autoRefresh: window.AppConfig?.app_auto_refresh !== false
    },
    
    // Confidence levels and thresholds
    confidence: {
        extremelyLow: 2,
        low: 4,
        medium: 6,
        high: 8,
        veryHigh: 10
    },
    
    // Time formats
    timeFormats: {
        age: {
            second: 1000,
            minute: 60000,
            hour: 3600000,
            day: 86400000
        }
    },
    
    // CSS classes for dynamic styling
    cssClasses: {
        confidence: {
            extremelyLow: 'confidence-extremely-low',
            low: 'confidence-low',
            medium: 'confidence-medium',
            high: 'confidence-high',
            veryHigh: 'confidence-very-high'
        },
        status: {
            pending: 'text-warning',
            processing: 'text-info',
            completed: 'text-success',
            error: 'text-danger'
        }
    },
    
    // Icon mappings
    icons: {
        news: 'bi-file-text',
        ideas: 'bi-lightbulb',
        opinions: 'bi-chat-text',
        ai: 'bi-stars',
        loading: 'spinner-border spinner-border-sm'
    }
};
