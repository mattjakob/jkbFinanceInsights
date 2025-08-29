/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │            UTILITIES                │
 *  └─────────────────────────────────────┘
 *  Common utility functions for the application
 * 
 *  Provides reusable functions for date formatting, DOM manipulation,
 *  and other common operations.
 * 
 *  Parameters:
 *  - None
 * 
 *  Returns:
 *  - Utility functions object
 * 
 *  Notes:
 *  - Pure functions with no side effects
 *  - Used throughout the application
 */

import { config } from './config.js';

/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │         CALCULATE AGE               │
 *  └─────────────────────────────────────┘
 *  Calculates and formats age from timestamp
 * 
 *  Parameters:
 *  - timePosted: ISO timestamp string
 * 
 *  Returns:
 *  - Formatted age string
 */
export function calculateAge(timePosted) {
    if (!timePosted) return 'Unknown';
    
    const posted = new Date(timePosted);
    const now = new Date();
    const diff = now - posted;
    
    const { second, minute, hour, day } = config.timeFormats.age;
    
    if (diff < minute) {
        const seconds = Math.floor(diff / second);
        return `${seconds}s ago`;
    } else if (diff < hour) {
        const minutes = Math.floor(diff / minute);
        return `${minutes}m ago`;
    } else if (diff < day) {
        const hours = Math.floor(diff / hour);
        return `${hours}h ago`;
    } else {
        const days = Math.floor(diff / day);
        return `${days}d ago`;
    }
}

/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │      CALCULATE HORIZON              │
 *  └─────────────────────────────────────┘
 *  Calculates and formats time horizon from timestamp
 * 
 *  Shows time length from now with + for future and - for past
 * 
 *  Parameters:
 *  - eventTime: ISO timestamp string
 * 
 *  Returns:
 *  - Formatted horizon string
 */
export function calculateHorizon(eventTime) {
    if (!eventTime) return '-';
    
    const event = new Date(eventTime);
    const now = new Date();
    const diff = event - now; // Positive for future, negative for past
    
    // Use direct values instead of destructuring to avoid potential issues
    const second = 1000;
    const minute = 60000;
    const hour = 3600000;
    const day = 86400000;
    
    // Determine prefix and absolute difference
    const prefix = diff >= 0 ? '+' : '-';
    const absDiff = Math.abs(diff);
    
    if (absDiff < minute) {
        const seconds = Math.floor(absDiff / second);
        return `${prefix}${seconds}s`;
    } else if (absDiff < hour) {
        const minutes = Math.floor(absDiff / minute);
        return `${prefix}${minutes}m`;
    } else if (absDiff < day) {
        const hours = Math.floor(absDiff / hour);
        return `${prefix}${hours}h`;
    } else {
        const days = Math.floor(absDiff / day);
        return `${prefix}${days}d`;
    }
}

/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │       FORMAT EVENT TIME             │
 *  └─────────────────────────────────────┘
 *  Formats event time for display
 * 
 *  Parameters:
 *  - eventTime: Event time data structure
 * 
 *  Returns:
 *  - HTML formatted string
 */
export function formatEventTime(eventTime) {
    if (!eventTime || typeof eventTime !== 'object') {
        return '<span class="text-muted">-</span>';
    }
    
    // Extract values with defaults
    const stop = eventTime.stop || '-';
    const target = eventTime.target || '-';
    
    // Format HTML
    return `
        <div class="event-time-display">
            <small>
                <span class="text-danger">Stop: ${stop}</span><br>
                <span class="text-success">Target: ${target}</span>
            </small>
        </div>
    `;
}

/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │         FORMAT LEVELS               │
 *  └─────────────────────────────────────┘
 *  Formats price levels for display
 * 
 *  Parameters:
 *  - levels: Levels data structure
 * 
 *  Returns:
 *  - HTML formatted string
 */
export function formatLevels(levels) {
    if (!levels || typeof levels !== 'object') {
        return '<span class="text-muted">-</span>';
    }
    
    const support = levels.support || '-';
    const resistance = levels.resistance || '-';
    
    return `
        <div class="levels-display">
            <small>
                <span class="text-success">S: ${support}</span><br>
                <span class="text-danger">R: ${resistance}</span>
            </small>
        </div>
    `;
}

/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │       FORMAT TIMESTAMP              │
 *  └─────────────────────────────────────┘
 *  Formats timestamp for display
 * 
 *  Parameters:
 *  - timestamp: ISO timestamp string
 * 
 *  Returns:
 *  - Formatted date/time string
 */
export function formatTimestamp(timestamp) {
    if (!timestamp) return '-';
    
    const date = new Date(timestamp);
    const now = new Date();
    const diffHours = Math.abs(now - date) / 36e5;
    
    // If within 24 hours, show time only
    if (diffHours < 24) {
        return date.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit'
        });
    }
    
    // Otherwise show date and time
    return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │      GET CONFIDENCE CLASS           │
 *  └─────────────────────────────────────┘
 *  Gets CSS class for confidence level
 * 
 *  Parameters:
 *  - confidence: Confidence value (0-10)
 * 
 *  Returns:
 *  - CSS class name
 */
export function getConfidenceClass(confidence) {
    const level = parseInt(confidence) || 0;
    const { confidence: levels } = config;
    const { confidence: classes } = config.cssClasses;
    
    if (level <= levels.extremelyLow) return classes.extremelyLow;
    if (level <= levels.low) return classes.low;
    if (level <= levels.medium) return classes.medium;
    if (level < levels.high) return classes.high;
    return classes.veryHigh;
}

/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │         DEBOUNCE                    │
 *  └─────────────────────────────────────┘
 *  Creates a debounced function
 * 
 *  Parameters:
 *  - func: Function to debounce
 *  - delay: Delay in milliseconds
 * 
 *  Returns:
 *  - Debounced function
 */
export function debounce(func, delay) {
    let timeoutId;
    return function(...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => func.apply(this, args), delay);
    };
}



/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │         SAFE PARSE JSON             │
 *  └─────────────────────────────────────┘
 *  Safely parses JSON with error handling
 * 
 *  Parameters:
 *  - text: JSON string to parse
 *  - defaultValue: Default value if parsing fails
 * 
 *  Returns:
 *  - Parsed object or default value
 */
export function safeParseJSON(text, defaultValue = null) {
    try {
        return JSON.parse(text);
    } catch (error) {
        console.error('JSON parse error:', error);
        return defaultValue;
    }
}



