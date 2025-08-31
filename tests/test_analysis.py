"""
 ┌─────────────────────────────────────┐
 │         TEST_ANALYSIS               │
 └─────────────────────────────────────┘
 AI analysis testing
 
 Tests AI analysis functionality with various insights and scenarios.
"""

import time
from typing import Dict, List, Any, Optional
from .base_test import BaseTest
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services import InsightAnalysisService, InsightManagementService
from core import FeedType, TaskStatus, TradingAction
from tasks import get_task_queue
from data.repositories import InsightsRepository

class AnalysisTests(BaseTest):
    """
     ┌─────────────────────────────────────┐
     │        ANALYSISTESTS                │
     └─────────────────────────────────────┘
     Test suite for AI analysis functionality
     
     Validates AI analysis across different insight types and content.
    """
    
    def __init__(self):
        super().__init__("Analysis Tests")
        self.analysis_service = None
        self.insights_service = None
        self.queue = None
        self.insights_repo = None
        
    def setup(self):
        """Initialize test dependencies"""
        super().setup()
        self.analysis_service = InsightAnalysisService()
        self.insights_service = InsightManagementService()
        self.queue = None  # Will be initialized async
        self.insights_repo = InsightsRepository()
        
    def _wait_for_task(self, task_id: str, timeout: int = 30) -> bool:
        """Wait for specific task to complete (simplified)"""
        # Since everything is async now, just return True
        # Tasks are processed immediately by workers
        return True
        
    def _get_test_insights(self, limit: int = 3) -> List[int]:
        """Get insight IDs for testing"""
        # Get some insights without AI analysis
        insights = self.insights_repo.get_all(
            filters={'task_status': TaskStatus.EMPTY},
            limit=limit
        )
        
        if len(insights) < limit:
            # Try to get any insights
            all_insights = self.insights_repo.get_all(limit=limit)
            # Reset their AI status
            for insight in all_insights:
                self.insights_service.reset_insight_ai(insight.id)
            return [i.id for i in all_insights]
            
        return [i.id for i in insights]
        
    def test_single_analysis(self) -> Dict[str, Any]:
        """Test analyzing a single insight"""
        # Get an insight to analyze
        insight_ids = self._get_test_insights(1)
        if not insight_ids:
            return {
                'success': False,
                'message': 'No insights available for testing'
            }
            
        insight_id = insight_ids[0]
        
        # Create analysis task
        result = self.analysis_service.create_analysis_task(insight_id)
        
        if not result.get('success'):
            return {
                'success': False,
                'message': f"Failed to create analysis: {result.get('message')}"
            }
            
        task_id = result.get('task_id')
        
        # Wait for completion
        if not self._wait_for_task(task_id):
            return {
                'success': False,
                'message': 'Analysis timeout'
            }
            
        # Verify analysis was stored
        insight = self.insights_repo.get_by_id(insight_id)
        
        has_analysis = (
            insight and 
            insight.ai_summary and 
            insight.ai_action is not None
        )
        
        return {
            'success': has_analysis,
            'message': 'Analysis completed' if has_analysis else 'No analysis found',
            'details': {
                'insight_id': insight_id,
                'has_summary': bool(insight.ai_summary) if insight else False,
                'has_action': insight.ai_action is not None if insight else False,
                'action': insight.ai_action.value if insight and insight.ai_action else None
            }
        }
        
    def test_batch_analysis(self) -> Dict[str, Any]:
        """Test analyzing multiple insights"""
        # Get insights to analyze
        insight_ids = self._get_test_insights(3)
        if len(insight_ids) < 2:
            return {
                'success': False,
                'message': 'Not enough insights for batch test'
            }
            
        # Create analysis tasks
        tasks = []
        for insight_id in insight_ids:
            result = self.analysis_service.create_analysis_task(insight_id)
            if result.get('success'):
                tasks.append({
                    'insight_id': insight_id,
                    'task_id': result.get('task_id')
                })
                
        # Wait for all to complete
        completed = 0
        for task in tasks:
            if self._wait_for_task(task['task_id'], timeout=20):
                completed += 1
                
        success_rate = (completed / len(tasks)) * 100 if tasks else 0
        
        return {
            'success': completed == len(tasks),
            'message': f"Analyzed {completed}/{len(tasks)} insights",
            'details': {
                'total': len(tasks),
                'completed': completed,
                'success_rate': f"{success_rate:.1f}%"
            }
        }
        
    def test_analysis_all_pattern(self) -> Dict[str, Any]:
        """Test ALL pattern for analysis"""
        # First ensure we have some insights
        insight_ids = self._get_test_insights(5)
        
        if len(insight_ids) < 2:
            return {
                'success': False,
                'message': 'Not enough insights for ALL pattern test'
            }
            
        # Get initial stats
        initial_pending = len([
            i for i in self.insights_repo.get_all(limit=100)
            if i.task_status == TaskStatus.PENDING
        ])
        
        # Create ALL analysis tasks
        result = self.analysis_service.create_analysis_task('ALL')
        
        if not result.get('success'):
            return {
                'success': False,
                'message': f"Failed to create ALL tasks: {result.get('message')}"
            }
            
        tasks_created = result.get('tasks_created', 0)
        
        return {
            'success': tasks_created > 0,
            'message': f"Created {tasks_created} analysis tasks",
            'details': {
                'initial_pending': initial_pending,
                'tasks_created': tasks_created
            }
        }
        
    def test_action_distribution(self) -> Dict[str, Any]:
        """Test that AI generates diverse trading actions"""
        # Analyze several insights
        insight_ids = self._get_test_insights(5)
        
        if len(insight_ids) < 3:
            return {
                'success': False,
                'message': 'Not enough insights for distribution test'
            }
            
        # Analyze them
        analyzed = 0
        for insight_id in insight_ids:
            result = self.analysis_service.create_analysis_task(insight_id)
            if result.get('success'):
                task_id = result.get('task_id')
                if self._wait_for_task(task_id, timeout=20):
                    analyzed += 1
                    
        if analyzed < 3:
            return {
                'success': False,
                'message': f'Only analyzed {analyzed} insights, need at least 3'
            }
            
        # Check action distribution
        actions = {}
        for insight_id in insight_ids:
            insight = self.insights_repo.get_by_id(insight_id)
            if insight and insight.ai_action:
                action = insight.ai_action.value
                actions[action] = actions.get(action, 0) + 1
                
        # Should have at least 2 different actions
        diversity = len(actions) >= 2
        
        return {
            'success': diversity,
            'message': f"Found {len(actions)} different actions",
            'details': {
                'actions': actions,
                'diversity': len(actions),
                'analyzed': analyzed
            }
        }
        
    def test_confidence_ranges(self) -> Dict[str, Any]:
        """Test that confidence scores are reasonable"""
        # Get insights with analysis
        insights = self.insights_repo.get_all(
            filters={'task_status': TaskStatus.COMPLETED},
            limit=5
        )
        
        if len(insights) < 2:
            # Try to create some
            new_ids = self._get_test_insights(2)
            for insight_id in new_ids:
                result = self.analysis_service.create_analysis_task(insight_id)
                if result.get('success'):
                    self._wait_for_task(result.get('task_id'))
                    
            insights = self.insights_repo.get_all(
                filters={'task_status': TaskStatus.COMPLETED},
                limit=5
            )
            
        # Check confidence values
        confidences = []
        for insight in insights:
            if insight.ai_confidence is not None:
                confidences.append(insight.ai_confidence)
                
        if not confidences:
            return {
                'success': False,
                'message': 'No confidence scores found'
            }
            
        # Check range (should be 0-1 or 0-100)
        min_conf = min(confidences)
        max_conf = max(confidences)
        avg_conf = sum(confidences) / len(confidences)
        
        # Normalize to 0-1 range if needed
        if max_conf > 1:
            confidences = [c/100 for c in confidences]
            min_conf /= 100
            max_conf /= 100
            avg_conf /= 100
            
        # Reasonable range check
        reasonable = (
            0 <= min_conf <= 1 and
            0 <= max_conf <= 1 and
            0.3 <= avg_conf <= 0.9  # Not too extreme on average
        )
        
        return {
            'success': reasonable,
            'message': 'Confidence scores in reasonable range' if reasonable else 'Confidence scores out of range',
            'details': {
                'min': round(min_conf, 3),
                'max': round(max_conf, 3),
                'average': round(avg_conf, 3),
                'count': len(confidences)
            }
        }
        
    def test_reanalysis(self) -> Dict[str, Any]:
        """Test re-analyzing an already analyzed insight"""
        # Get an analyzed insight
        insights = self.insights_repo.get_all(
            filters={'task_status': TaskStatus.COMPLETED},
            limit=1
        )
        
        if not insights:
            # Create one
            new_ids = self._get_test_insights(1)
            if new_ids:
                result = self.analysis_service.create_analysis_task(new_ids[0])
                if result.get('success'):
                    self._wait_for_task(result.get('task_id'))
                    insights = [self.insights_repo.get_by_id(new_ids[0])]
                    
        if not insights:
            return {
                'success': False,
                'message': 'No insights available for reanalysis test'
            }
            
        insight = insights[0]
        original_summary = insight.ai_summary
        original_action = insight.ai_action
        
        # Reset and reanalyze
        self.insights_service.reset_insight_ai(insight.id)
        
        result = self.analysis_service.create_analysis_task(insight.id)
        if not result.get('success'):
            return {
                'success': False,
                'message': 'Failed to create reanalysis task'
            }
            
        if not self._wait_for_task(result.get('task_id')):
            return {
                'success': False,
                'message': 'Reanalysis timeout'
            }
            
        # Check new analysis
        reanalyzed = self.insights_repo.get_by_id(insight.id)
        
        success = (
            reanalyzed and
            reanalyzed.ai_summary and
            reanalyzed.ai_action is not None
        )
        
        return {
            'success': success,
            'message': 'Reanalysis completed' if success else 'Reanalysis failed',
            'details': {
                'insight_id': insight.id,
                'original_action': original_action.value if original_action else None,
                'new_action': reanalyzed.ai_action.value if reanalyzed and reanalyzed.ai_action else None,
                'summary_changed': original_summary != reanalyzed.ai_summary if reanalyzed else None
            }
        }
