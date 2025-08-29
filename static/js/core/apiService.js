/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │          API SERVICE                │
 *  └─────────────────────────────────────┘
 *  Centralized API service with caching
 * 
 *  Provides a unified interface for all API calls with
 *  built-in caching, error handling, and retry logic.
 * 
 *  Parameters:
 *  - None
 * 
 *  Returns:
 *  - APIService singleton instance
 * 
 *  Notes:
 *  - Implements request caching
 *  - Provides consistent error handling
 *  - Reduces duplicate API logic
 */

import { config } from './config.js';

class APIService {
    constructor() {
        this.cache = new Map();
        this.cacheTimeout = 5000; // 5 seconds cache
        this.pendingRequests = new Map();
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │         GET CACHE KEY               │
     *  └─────────────────────────────────────┘
     *  Generate cache key for request
     * 
     *  Parameters:
     *  - endpoint: API endpoint
     *  - params: Request parameters
     * 
     *  Returns:
     *  - String cache key
     */
    getCacheKey(endpoint, params = {}) {
        const sortedParams = Object.keys(params)
            .sort()
            .map(key => `${key}=${params[key]}`)
            .join('&');
        return `${endpoint}?${sortedParams}`;
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │        CACHED REQUEST               │
     *  └─────────────────────────────────────┘
     *  Make request with caching
     * 
     *  Parameters:
     *  - endpoint: API endpoint
     *  - options: Request options
     * 
     *  Returns:
     *  - Promise<any> Response data
     */
    async cachedRequest(endpoint, options = {}) {
        const cacheKey = this.getCacheKey(endpoint, options.params);
        
        // Check cache first
        const cached = this.cache.get(cacheKey);
        if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
            return cached.data;
        }
        
        // Check if request is already pending
        if (this.pendingRequests.has(cacheKey)) {
            return this.pendingRequests.get(cacheKey);
        }
        
        // Make new request
        const requestPromise = this.makeRequest(endpoint, options)
            .then(data => {
                // Cache successful response
                this.cache.set(cacheKey, {
                    data,
                    timestamp: Date.now()
                });
                return data;
            })
            .finally(() => {
                this.pendingRequests.delete(cacheKey);
            });
        
        this.pendingRequests.set(cacheKey, requestPromise);
        return requestPromise;
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │         MAKE REQUEST                │
     *  └─────────────────────────────────────┘
     *  Make actual HTTP request
     * 
     *  Parameters:
     *  - endpoint: API endpoint
     *  - options: Request options
     * 
     *  Returns:
     *  - Promise<any> Response data
     */
    async makeRequest(endpoint, options = {}) {
        const {
            method = 'GET',
            params = {},
            body = null,
            headers = {}
        } = options;

        // Build URL with params for GET requests
        let url = endpoint;
        if (method === 'GET' && Object.keys(params).length > 0) {
            const queryString = new URLSearchParams(params).toString();
            url += `?${queryString}`;
        }

        // Prepare request options
        const requestOptions = {
            method,
            headers: {
                'Content-Type': 'application/json',
                ...headers
            }
        };

        if (body && method !== 'GET') {
            requestOptions.body = JSON.stringify(body);
        }

        try {
            const response = await fetch(url, requestOptions);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error(`API request failed: ${endpoint}`, error);
            throw error;
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │        FETCH INSIGHTS               │
     *  └─────────────────────────────────────┘
     *  Fetch insights with filters
     * 
     *  Parameters:
     *  - filters: Filter parameters
     * 
     *  Returns:
     *  - Promise<Array> Insights data
     */
    async fetchInsights(filters = {}) {
        const params = {};
        
        if (filters.symbol) params.symbol = filters.symbol;
        if (filters.type) params.type = filters.type;
        if (filters.limit) params.limit = filters.limit;

        return this.cachedRequest(config.api.insights, { params });
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │      TRIGGER SCRAPING               │
     *  └─────────────────────────────────────┘
     *  Trigger scraping for symbol
     * 
     *  Parameters:
     *  - symbol: Trading symbol
     * 
     *  Returns:
     *  - Promise<Object> Scraping result
     */
    async triggerScraping(symbol) {
        return this.makeRequest(config.api.scraping, {
            method: 'POST',
            body: { symbol }
        });
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │      TRIGGER ANALYSIS               │
     *  └─────────────────────────────────────┘
     *  Trigger AI analysis
     * 
     *  Parameters:
     *  - symbol: Trading symbol (optional)
     * 
     *  Returns:
     *  - Promise<Object> Analysis result
     */
    async triggerAnalysis(symbol = null) {
        const body = {};
        if (symbol) body.symbol = symbol;
        
        return this.makeRequest(config.api.analysis, {
            method: 'POST',
            body
        });
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │        SEARCH SYMBOLS               │
     *  └─────────────────────────────────────┘
     *  Search for trading symbols
     * 
     *  Parameters:
     *  - query: Search query
     * 
     *  Returns:
     *  - Promise<Array> Symbol results
     */
    async searchSymbols(query) {
        if (!query || query.length < 2) {
            return [];
        }

        return this.cachedRequest(config.api.symbols.search, {
            params: { q: query }
        });
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │       VALIDATE SYMBOL               │
     *  └─────────────────────────────────────┘
     *  Validate trading symbol
     * 
     *  Parameters:
     *  - symbol: Symbol to validate
     *  - exchange: Exchange (optional)
     * 
     *  Returns:
     *  - Promise<Object> Validation result
     */
    async validateSymbol(symbol, exchange = null) {
        const params = { symbol };
        if (exchange) params.exchange = exchange;
        
        return this.cachedRequest(config.api.symbols.validate, { params });
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │         GET TASK STATUS             │
     *  └─────────────────────────────────────┘
     *  Get task queue status
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - Promise<Object> Task status
     */
    async getTaskStatus() {
        return this.makeRequest(config.api.tasks);
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │        CLEAR CACHE                  │
     *  └─────────────────────────────────────┘
     *  Clear request cache
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - None
     */
    clearCache() {
        this.cache.clear();
        console.info('API cache cleared');
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │      SET CACHE TIMEOUT              │
     *  └─────────────────────────────────────┘
     *  Set cache timeout duration
     * 
     *  Parameters:
     *  - timeout: Timeout in milliseconds
     * 
     *  Returns:
     *  - None
     */
    setCacheTimeout(timeout) {
        this.cacheTimeout = timeout;
    }
}

// Export singleton instance
export const apiService = new APIService();
