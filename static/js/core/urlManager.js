/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │          URL MANAGER                │
 *  └─────────────────────────────────────┘
 *  Centralized URL and path management
 * 
 *  Provides consistent URL parsing and building logic
 *  to eliminate duplicate path handling code.
 * 
 *  Parameters:
 *  - None
 * 
 *  Returns:
 *  - URLManager static class
 * 
 *  Notes:
 *  - Single source of truth for URL logic
 *  - Handles all path parsing
 *  - Consistent filter extraction
 */

export class URLManager {
    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │     PARSE CURRENT FILTERS           │
     *  └─────────────────────────────────────┘
     *  Parse filters from current URL
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - Object with filters
     */
    static parseCurrentFilters() {
        const pathParts = window.location.pathname.split('/').filter(p => p);
        const filters = {
            symbol: '',
            exchange: '',
            type: ''
        };

        // Check if we're on a filtered route
        if (pathParts[0] === 'api' && pathParts[1] === 'insights' && pathParts[2]) {
            const exchangeSymbol = pathParts[2];
            
            // Parse exchange:symbol format
            if (exchangeSymbol.includes(':')) {
                const [exchange, symbol] = exchangeSymbol.split(':', 2);
                filters.exchange = exchange;
                filters.symbol = symbol;
            } else {
                filters.symbol = exchangeSymbol;
            }
            
            // Parse type filter
            if (pathParts[3]) {
                filters.type = pathParts[3].replace(/_/g, ' ');
            }
        }

        return filters;
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │      BUILD INSIGHTS URL             │
     *  └─────────────────────────────────────┘
     *  Build URL for insights with filters
     * 
     *  Parameters:
     *  - filters: Filter object
     * 
     *  Returns:
     *  - String URL path
     */
    static buildInsightsURL(filters = {}) {
        const { symbol, exchange, type } = filters;
        
        // Base path
        let path = '/';
        
        // Add symbol/exchange filter
        if (symbol) {
            const exchangeSymbol = exchange ? `${exchange}:${symbol}` : symbol;
            path = `/api/insights/${exchangeSymbol}`;
            
            // Add type filter
            if (type) {
                const urlSafeType = type.replace(/\s+/g, '_');
                path += `/${urlSafeType}`;
            }
        }
        
        return path;
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │        NAVIGATE TO                  │
     *  └─────────────────────────────────────┘
     *  Navigate to URL if different
     * 
     *  Parameters:
     *  - url: Target URL
     *  - force: Force navigation
     * 
     *  Returns:
     *  - Boolean if navigated
     */
    static navigateTo(url, force = false) {
        if (!force && window.location.pathname === url) {
            return false;
        }
        
        window.location.href = url;
        return true;
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │     UPDATE QUERY PARAMS             │
     *  └─────────────────────────────────────┘
     *  Update URL query parameters
     * 
     *  Parameters:
     *  - params: Parameters to update
     * 
     *  Returns:
     *  - None
     */
    static updateQueryParams(params = {}) {
        const url = new URL(window.location);
        
        // Update or remove parameters
        Object.entries(params).forEach(([key, value]) => {
            if (value === null || value === undefined) {
                url.searchParams.delete(key);
            } else {
                url.searchParams.set(key, value);
            }
        });
        
        // Update URL without reload
        window.history.replaceState({}, '', url);
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │       GET QUERY PARAM               │
     *  └─────────────────────────────────────┘
     *  Get query parameter value
     * 
     *  Parameters:
     *  - key: Parameter key
     *  - defaultValue: Default value
     * 
     *  Returns:
     *  - String parameter value
     */
    static getQueryParam(key, defaultValue = null) {
        const params = new URLSearchParams(window.location.search);
        return params.get(key) || defaultValue;
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │    GET ALL QUERY PARAMS             │
     *  └─────────────────────────────────────┘
     *  Get all query parameters
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - Object with all parameters
     */
    static getAllQueryParams() {
        const params = new URLSearchParams(window.location.search);
        const result = {};
        
        for (const [key, value] of params) {
            result[key] = value;
        }
        
        return result;
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │      IS FILTERED ROUTE              │
     *  └─────────────────────────────────────┘
     *  Check if current route has filters
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - Boolean
     */
    static isFilteredRoute() {
        const path = window.location.pathname;
        return path.includes('/api/insights/') && path !== '/api/insights/';
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │       RELOAD WITH DELAY             │
     *  └─────────────────────────────────────┘
     *  Reload page after delay
     * 
     *  Parameters:
     *  - delay: Delay in milliseconds
     * 
     *  Returns:
     *  - None
     */
    static reloadWithDelay(delay = 1000) {
        setTimeout(() => {
            window.location.reload();
        }, delay);
    }
}

// Export as default
export default URLManager;
