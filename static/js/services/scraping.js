/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │        SCRAPING SERVICE             │
 *  └─────────────────────────────────────┘
 *  Service for managing data scraping operations
 * 
 *  Handles fetching new insights from external sources
 *  through the scraping API endpoints.
 * 
 *  Parameters:
 *  - None
 * 
 *  Returns:
 *  - ScrapingService class
 * 
 *  Notes:
 *  - Manages feed types and scraping requests
 *  - Provides status tracking for scraping operations
 */

import { apiClient } from '../core/api.js';
import { config } from '../core/config.js';

class ScrapingService {
    constructor() {
        this.availableFeeds = [];
        this.lastFetchStatus = null;
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │         FETCH INSIGHTS              │
     *  └─────────────────────────────────────┘
     *  Fetches new insights from external sources
     * 
     *  Parameters:
     *  - symbol: Trading symbol
     *  - exchange: Exchange name
     *  - feedType: Type of feed to scrape
     *  - maxItems: Maximum number of items
     * 
     *  Returns:
     *  - Fetch operation result
     */
    async fetchInsights({ symbol, exchange, feedType = '', maxItems = 10 }) {
        const requestBody = {
            symbol: symbol.toUpperCase(),
            exchange: exchange.toUpperCase(),
            feed_type: feedType,
            max_items: parseInt(maxItems)
        };
        
        try {
            const result = await apiClient.post(`${config.api.scraping}/fetch`, requestBody);
            this.lastFetchStatus = result;
            return result;
        } catch (error) {
            console.error('Error fetching insights:', error);
            throw error;
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │       GET AVAILABLE FEEDS           │
     *  └─────────────────────────────────────┘
     *  Gets list of available feed types
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - Array of feed types
     */
    async getAvailableFeeds() {
        try {
            const data = await apiClient.get(`${config.api.scraping}/feeds`);
            this.availableFeeds = data.feeds || [];
            return this.availableFeeds;
        } catch (error) {
            console.error('Error fetching available feeds:', error);
            return this.availableFeeds;
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │      GET LAST FETCH STATUS          │
     *  └─────────────────────────────────────┘
     *  Gets the status of the last fetch operation
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - Last fetch status object
     */
    getLastFetchStatus() {
        return this.lastFetchStatus;
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │      VALIDATE FEED TYPE             │
     *  └─────────────────────────────────────┘
     *  Validates if a feed type is available
     * 
     *  Parameters:
     *  - feedType: Feed type to validate
     * 
     *  Returns:
     *  - Boolean indicating validity
     */
    isValidFeedType(feedType) {
        if (!feedType) return true; // Empty means all feeds
        return this.availableFeeds.includes(feedType);
    }
}

// Export singleton instance
export const scrapingService = new ScrapingService();



