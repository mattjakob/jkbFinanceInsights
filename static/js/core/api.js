/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │             API CLIENT              │
 *  └─────────────────────────────────────┘
 *  Centralized API client for all backend communication
 * 
 *  Provides a consistent interface for making API calls with
 *  error handling, request/response transformation, and logging.
 * 
 *  Parameters:
 *  - None
 * 
 *  Returns:
 *  - ApiClient class
 * 
 *  Notes:
 *  - Handles JSON serialization/deserialization
 *  - Provides consistent error handling
 *  - Supports all HTTP methods
 */

class ApiClient {
    constructor(baseUrl = '') {
        this.baseUrl = baseUrl;
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │            REQUEST                  │
     *  └─────────────────────────────────────┘
     *  Makes an HTTP request to the API
     * 
     *  Parameters:
     *  - url: API endpoint URL
     *  - options: Fetch options (method, headers, body, etc.)
     * 
     *  Returns:
     *  - Promise resolving to response data
     * 
     *  Notes:
     *  - Automatically adds JSON headers for POST/PUT requests
     *  - Handles response parsing
     */
    async request(url, options = {}) {
        const fullUrl = this.baseUrl + url;
        
        // Set default headers
        const headers = {
            ...options.headers
        };
        
        // Add JSON headers for requests with body
        if (options.body && typeof options.body === 'object') {
            headers['Content-Type'] = 'application/json';
            options.body = JSON.stringify(options.body);
        }
        
        try {
            const response = await fetch(fullUrl, {
                ...options,
                headers
            });
            
            // Parse response
            const data = await response.json();
            
            if (!response.ok) {
                throw new ApiError(response.status, data.message || 'API request failed', data);
            }
            
            return data;
        } catch (error) {
            if (error instanceof ApiError) {
                throw error;
            }
            throw new ApiError(0, 'Network error', { originalError: error.message });
        }
    }

    // Convenience methods
    get(url, options = {}) {
        return this.request(url, { ...options, method: 'GET' });
    }

    post(url, body, options = {}) {
        return this.request(url, { ...options, method: 'POST', body });
    }

    put(url, body, options = {}) {
        return this.request(url, { ...options, method: 'PUT', body });
    }

    delete(url, options = {}) {
        return this.request(url, { ...options, method: 'DELETE' });
    }
}

/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │            API ERROR                │
 *  └─────────────────────────────────────┘
 *  Custom error class for API errors
 * 
 *  Parameters:
 *  - status: HTTP status code
 *  - message: Error message
 *  - data: Additional error data
 * 
 *  Returns:
 *  - ApiError instance
 */
class ApiError extends Error {
    constructor(status, message, data = {}) {
        super(message);
        this.name = 'ApiError';
        this.status = status;
        this.data = data;
    }
}

// Export singleton instance
const apiClient = new ApiClient();
export { apiClient, ApiError };



