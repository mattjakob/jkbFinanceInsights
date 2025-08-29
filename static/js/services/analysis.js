/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │        ANALYSIS SERVICE             │
 *  └─────────────────────────────────────┘
 *  Service for managing AI analysis operations
 * 
 *  Handles triggering AI analysis for insights and
 *  tracking analysis status.
 * 
 *  Parameters:
 *  - None
 * 
 *  Returns:
 *  - AnalysisService class
 * 
 *  Notes:
 *  - Manages AI analysis requests
 *  - Provides status tracking
 */

import { apiClient } from '../core/api.js';
import { config } from '../core/config.js';

class AnalysisService {
    constructor() {
        this.lastAnalysisStatus = null;
        this.isAnalyzing = false;
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │       TRIGGER ANALYSIS              │
     *  └─────────────────────────────────────┘
     *  Triggers AI analysis for pending insights
     * 
     *  Parameters:
     *  - filters: Object with symbol and/or type filters, or just symbol string (backward compatible)
     * 
     *  Returns:
     *  - Analysis operation result
     */
    async triggerAnalysis(filters = null) {
        if (this.isAnalyzing) {
            throw new Error('Analysis already in progress');
        }
        
        this.isAnalyzing = true;
        
        try {
            let requestBody = {};
            
            // Handle backward compatibility (string symbol) and new object format
            if (typeof filters === 'string') {
                requestBody = { symbol: filters };
            } else if (filters && typeof filters === 'object') {
                if (filters.symbol) requestBody.symbol = filters.symbol;
                if (filters.type) requestBody.type = filters.type;
            }
            
            console.log('Analysis service sending request:', requestBody);
            const result = await apiClient.post(`${config.api.analysis}/analyze`, requestBody);
            this.lastAnalysisStatus = result;
            return result;
        } catch (error) {
            console.error('Error triggering analysis:', error);
            throw error;
        } finally {
            this.isAnalyzing = false;
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │      GET ANALYSIS STATUS            │
     *  └─────────────────────────────────────┘
     *  Gets current analysis status
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - Analysis status object
     */
    async getAnalysisStatus() {
        try {
            const status = await apiClient.get(`${config.api.analysis}/status`);
            return status;
        } catch (error) {
            console.error('Error fetching analysis status:', error);
            return null;
        }
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │         IS ANALYZING                │
     *  └─────────────────────────────────────┘
     *  Checks if analysis is currently running
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - Boolean indicating analysis state
     */
    isCurrentlyAnalyzing() {
        return this.isAnalyzing;
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │    GET LAST ANALYSIS STATUS         │
     *  └─────────────────────────────────────┘
     *  Gets the status of the last analysis
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - Last analysis status object
     */
    getLastAnalysisStatus() {
        return this.lastAnalysisStatus;
    }
}

// Export singleton instance
export const analysisService = new AnalysisService();



