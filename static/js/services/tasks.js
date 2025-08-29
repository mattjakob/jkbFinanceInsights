/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │          TASKS SERVICE              │
 *  └─────────────────────────────────────┘
 *  Service for managing task operations
 * 
 *  Handles task status monitoring and statistics
 *  for the task queue system.
 * 
 *  Parameters:
 *  - None
 * 
 *  Returns:
 *  - TasksService class
 * 
 *  Notes:
 *  - Monitors running, queued, and failed tasks
 *  - Provides real-time task statistics
 */

import { apiClient } from '../core/api.js';
import { config } from '../core/config.js';



class TasksService {
    constructor() {
        this.stats = {
            pending: 0,
            processing: 0,
            completed: 0,
            failed: 0,
            cancelled: 0
        };
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │         FETCH TASK STATS            │
     *  └─────────────────────────────────────┘
     *  Fetches current task statistics
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - Task statistics object
     */
    async fetchTaskStats() {
        try {
            const response = await apiClient.get('/api/tasks/stats');
            this.stats = response.stats || this.stats;
            return this.stats;
        } catch (error) {
            console.error('Error fetching task stats:', error);
            return this.stats;
        }
    }



    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │         GET CURRENT STATS           │
     *  └─────────────────────────────────────┘
     *  Gets current task statistics
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - Current task statistics
     */
    getCurrentStats() {
        return { ...this.stats };
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │         HAS ACTIVE TASKS            │
     *  └─────────────────────────────────────┘
     *  Checks if there are any active tasks
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - Boolean indicating if there are active tasks
     */
    hasActiveTasks() {
        return this.stats.pending > 0 || this.stats.processing > 0;
    }

    /**
     * 
     *  ┌─────────────────────────────────────┐
     *  │         HAS FAILED TASKS            │
     *  └─────────────────────────────────────┘
     *  Checks if there are any failed tasks
     * 
     *  Parameters:
     *  - None
     * 
     *  Returns:
     *  - Boolean indicating if there are failed tasks
     */
    hasFailedTasks() {
        return this.stats.failed > 0;
    }
}

// Export singleton instance
export const tasksService = new TasksService();
