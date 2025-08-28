/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │        INSIGHTS SERVICE             │
 *  └─────────────────────────────────────┘
 *  Service for managing insights data
 * 
 *  Handles all insights-related API calls and data management,
 *  including fetching, filtering, and updating insights.
 * 
 *  Parameters:
 *  - None
 * 
 *  Returns:
 *  - InsightsService class
 * 
 *  Notes:
 *  - Uses the centralized API client
 *  - Manages insights state and caching
 */

import { apiClient } from '../core/api.js';
import { config } from '../core/config.js';

class InsightsService {
    constructor() {
        this.cache = new Map();
        this.filters = {
            symbol: '',
            type: ''
        };
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │         FETCH INSIGHTS              │
     *  └─────────────────────────────────────┘
     *  Fetches insights from the API
     * 
     *  Parameters:
     *  - symbol: Optional symbol filter
     *  - type: Optional type filter
     * 
     *  Returns:
     *  - Array of insights
     */
    async fetchInsights(symbol = '', type = '') {
        const params = new URLSearchParams();
        if (symbol) params.append('symbol', symbol);
        if (type) params.append('type', type);
        
        const queryString = params.toString();
        const url = queryString ? `${config.api.insights}?${queryString}` : config.api.insights;
        
        try {
            const data = await apiClient.get(url);
            return data.insights || [];
        } catch (error) {
            console.error('Error fetching insights:', error);
            throw error;
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │         DELETE INSIGHTS             │
     *  └─────────────────────────────────────┘
     *  Deletes insights by type
     * 
     *  Parameters:
     *  - type: Type of insights to delete
     * 
     *  Returns:
     *  - Delete operation result
     */
    async deleteInsights(type) {
        const params = new URLSearchParams({ type });
        const url = `${config.api.insights}?${params}`;
        
        try {
            return await apiClient.delete(url);
        } catch (error) {
            console.error('Error deleting insights:', error);
            throw error;
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │         RESET AI ANALYSIS           │
     *  └─────────────────────────────────────┘
     *  Resets AI analysis for an insight
     * 
     *  Parameters:
     *  - insightId: ID of the insight
     * 
     *  Returns:
     *  - Reset operation result
     */
    async resetAIAnalysis(insightId) {
        const url = `${config.api.insights}/${insightId}/reset-ai`;
        
        try {
            return await apiClient.post(url, {});
        } catch (error) {
            console.error('Error resetting AI analysis:', error);
            throw error;
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │      GET INSIGHT BY ID              │
     *  └─────────────────────────────────────┘
     *  Gets a single insight by ID
     * 
     *  Parameters:
     *  - id: Insight ID
     * 
     *  Returns:
     *  - Insight object or null
     */
    async getInsightById(id) {
        // Check cache first
        if (this.cache.has(id)) {
            return this.cache.get(id);
        }
        
        try {
            const insights = await this.fetchInsights();
            const insight = insights.find(i => i.id === id);
            
            if (insight) {
                this.cache.set(id, insight);
            }
            
            return insight || null;
        } catch (error) {
            console.error('Error fetching insight by ID:', error);
            return null;
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │         UPDATE CACHE                │
     *  └─────────────────────────────────────┘
     *  Updates the insights cache
     * 
     *  Parameters:
     *  - insights: Array of insights to cache
     * 
     *  Returns:
     *  - None
     */
    updateCache(insights) {
        insights.forEach(insight => {
            this.cache.set(insight.id, insight);
        });
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │       DELETE SINGLE INSIGHT         │
     *  └─────────────────────────────────────┘
     *  Deletes a single insight by ID
     * 
     *  Parameters:
     *  - insightId: ID of the insight to delete
     *  - redirect: Whether to redirect after deletion
     * 
     *  Returns:
     *  - Delete operation result
     */
    async deleteInsight(insightId, redirect = false) {
        const url = `${config.api.insights}/${insightId}`;
        
        try {
            const result = await apiClient.delete(url);
            
            // Clear from cache
            this.cache.delete(insightId);
            
            if (redirect) {
                window.location.href = '/';
            }
            
            return result;
        } catch (error) {
            console.error('Error deleting insight:', error);
            throw error;
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │      PERFORM AI TEXT ANALYSIS       │
     *  └─────────────────────────────────────┘
     *  Triggers AI text analysis for an insight
     * 
     *  Parameters:
     *  - insightId: ID of the insight
     * 
     *  Returns:
     *  - Analysis operation result
     */
    async performAITextAnalysis(insightId) {
        const url = `${config.api.insights}/${insightId}/ai-text-analysis`;
        
        try {
            return await apiClient.post(url, {});
        } catch (error) {
            console.error('Error performing AI text analysis:', error);
            throw error;
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │      PERFORM AI IMAGE ANALYSIS      │
     *  └─────────────────────────────────────┘
     *  Triggers AI image analysis for an insight
     * 
     *  Parameters:
     *  - insightId: ID of the insight
     * 
     *  Returns:
     *  - Analysis operation result
     */
    async performAIImageAnalysis(insightId) {
        const url = `${config.api.insights}/${insightId}/ai-image-analysis`;
        
        try {
            return await apiClient.post(url, {});
        } catch (error) {
            console.error('Error performing AI image analysis:', error);
            throw error;
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │         CLEAR CACHE                 │
     *  └─────────────────────────────────────┘
     *  Clears the insights cache
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - None
     */
    clearCache() {
        this.cache.clear();
    }
}

// Export singleton instance
export const insightsService = new InsightsService();



