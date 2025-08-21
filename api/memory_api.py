#!/usr/bin/env python3
"""
VELOS Memory API
고급 메모리 시스템 API 엔드포인트

Provides:
- RESTful API for memory operations
- Real-time dashboard data
- Advanced search capabilities
- Analytics and insights endpoints
"""

import json
import time
from typing import Dict, List, Any, Optional
from pathlib import Path
import traceback

# VELOS integrations
try:
    from modules.memory.advanced.semantic_search import SemanticSearchEngine
    from modules.memory.advanced.memory_analytics import MemoryAnalytics
    from modules.memory.dashboard.memory_dashboard import MemoryDashboard
    from modules.core.security_validator import VelosSecurityValidator
except ImportError:
    # Fallback for standalone usage
    SemanticSearchEngine = None
    MemoryAnalytics = None
    MemoryDashboard = None
    VelosSecurityValidator = None


class MemoryAPI:
    """Advanced Memory System API"""
    
    def __init__(self):
        """Initialize API with all components"""
        self.search_engine = SemanticSearchEngine() if SemanticSearchEngine else None
        self.analytics = MemoryAnalytics() if MemoryAnalytics else None
        self.dashboard = MemoryDashboard() if MemoryDashboard else None
        self.security_validator = VelosSecurityValidator() if VelosSecurityValidator else None
        
        # API status
        self.api_version = "1.0.0"
        self.start_time = time.time()
    
    def _create_response(self, success: bool = True, data: Any = None, message: str = "", error: str = "") -> Dict:
        """Create standardized API response"""
        response = {
            'success': success,
            'timestamp': int(time.time()),
            'api_version': self.api_version
        }
        
        if success:
            response['data'] = data
            if message:
                response['message'] = message
        else:
            response['error'] = error
            if data:
                response['error_details'] = data
        
        return response
    
    def _validate_request(self, request_data: Dict) -> bool:
        """Validate incoming request"""
        if not self.security_validator:
            return True
        
        # Basic validation
        if 'query' in request_data:
            return self.security_validator.validate_search_query(request_data['query'])
        
        return True
    
    # ===========================================
    # SEARCH ENDPOINTS
    # ===========================================
    
    def search_memories(self, request_data: Dict) -> Dict:
        """
        Advanced memory search endpoint
        
        Expected request_data:
        {
            "query": "search terms",
            "limit": 20,
            "filters": {"role": "assistant", "date_from": 1234567890},
            "context": {"tags": ["important"], "preferred_roles": ["user"]}
        }
        """
        try:
            if not self._validate_request(request_data):
                return self._create_response(False, error="Invalid request")
            
            if not self.search_engine:
                return self._create_response(False, error="Search engine not available")
            
            query = request_data.get('query', '')
            limit = min(request_data.get('limit', 20), 100)  # Max 100 results
            filters = request_data.get('filters', {})
            context = request_data.get('context', {})
            
            if not query.strip():
                return self._create_response(False, error="Query cannot be empty")
            
            # Perform semantic search
            results = self.search_engine.semantic_search(
                query=query,
                limit=limit,
                context=context,
                filters=filters
            )
            
            # Format results for API response
            formatted_results = []
            for result in results:
                formatted_results.append({
                    'id': result.id,
                    'content': result.content,
                    'similarity_score': result.similarity_score,
                    'context_relevance': result.context_relevance,
                    'combined_score': result.combined_score,
                    'timestamp': result.timestamp,
                    'role': result.role,
                    'tags': result.tags,
                    'metadata': result.metadata
                })
            
            return self._create_response(True, {
                'query': query,
                'total_results': len(formatted_results),
                'results': formatted_results,
                'search_metadata': {
                    'semantic_search': True,
                    'filters_applied': filters,
                    'context_applied': bool(context)
                }
            })
            
        except Exception as e:
            return self._create_response(False, error=f"Search failed: {str(e)}")
    
    def get_related_memories(self, request_data: Dict) -> Dict:
        """
        Find memories related to a specific memory
        
        Expected request_data:
        {
            "memory_id": 123,
            "limit": 10,
            "similarity_threshold": 0.3
        }
        """
        try:
            if not self.search_engine:
                return self._create_response(False, error="Search engine not available")
            
            memory_id = request_data.get('memory_id')
            limit = min(request_data.get('limit', 10), 50)
            threshold = request_data.get('similarity_threshold', 0.3)
            
            if not memory_id:
                return self._create_response(False, error="memory_id is required")
            
            results = self.search_engine.get_related_memories(
                memory_id=memory_id,
                limit=limit,
                similarity_threshold=threshold
            )
            
            formatted_results = [
                {
                    'id': result.id,
                    'content': result.content,
                    'similarity_score': result.similarity_score,
                    'timestamp': result.timestamp,
                    'role': result.role,
                    'tags': result.tags
                }
                for result in results
            ]
            
            return self._create_response(True, {
                'reference_memory_id': memory_id,
                'related_memories': formatted_results,
                'total_found': len(formatted_results)
            })
            
        except Exception as e:
            return self._create_response(False, error=f"Related memories search failed: {str(e)}")
    
    # ===========================================
    # ANALYTICS ENDPOINTS
    # ===========================================
    
    def get_productivity_analysis(self, request_data: Dict) -> Dict:
        """
        Get productivity analysis
        
        Expected request_data:
        {
            "days_back": 30
        }
        """
        try:
            if not self.analytics:
                return self._create_response(False, error="Analytics engine not available")
            
            days_back = min(request_data.get('days_back', 30), 365)  # Max 1 year
            
            analysis = self.analytics.analyze_productivity_patterns(days_back)
            
            return self._create_response(True, analysis)
            
        except Exception as e:
            return self._create_response(False, error=f"Productivity analysis failed: {str(e)}")
    
    def get_content_trends(self, request_data: Dict) -> Dict:
        """
        Get trending topics and content patterns
        
        Expected request_data:
        {
            "days_back": 7,
            "min_frequency": 3
        }
        """
        try:
            if not self.analytics:
                return self._create_response(False, error="Analytics engine not available")
            
            days_back = min(request_data.get('days_back', 7), 90)
            min_frequency = request_data.get('min_frequency', 3)
            
            trends = self.analytics.detect_content_trends(
                days_back=days_back,
                min_frequency=min_frequency
            )
            
            # Format trends for API response
            formatted_trends = [
                {
                    'trend_type': trend.trend_type,
                    'description': trend.description,
                    'confidence': trend.confidence,
                    'keyword': trend.metadata['keyword'],
                    'total_frequency': trend.metadata['total_frequency'],
                    'trend_strength': trend.metadata['trend_strength'],
                    'data_points': trend.data_points
                }
                for trend in trends
            ]
            
            return self._create_response(True, {
                'trends': formatted_trends,
                'analysis_period_days': days_back,
                'total_trends_detected': len(formatted_trends)
            })
            
        except Exception as e:
            return self._create_response(False, error=f"Trend analysis failed: {str(e)}")
    
    def get_knowledge_graph(self, request_data: Dict) -> Dict:
        """
        Generate knowledge graph from memory data
        
        Expected request_data:
        {
            "days_back": 30,
            "max_nodes": 50
        }
        """
        try:
            if not self.analytics:
                return self._create_response(False, error="Analytics engine not available")
            
            days_back = min(request_data.get('days_back', 30), 365)
            max_nodes = min(request_data.get('max_nodes', 50), 200)
            
            graph_data = self.analytics.generate_knowledge_graph(
                days_back=days_back,
                max_nodes=max_nodes
            )
            
            return self._create_response(True, graph_data)
            
        except Exception as e:
            return self._create_response(False, error=f"Knowledge graph generation failed: {str(e)}")
    
    def get_memory_health(self, request_data: Dict) -> Dict:
        """
        Get memory system health score and recommendations
        
        Expected request_data:
        {
            "days_back": 30
        }
        """
        try:
            if not self.analytics:
                return self._create_response(False, error="Analytics engine not available")
            
            days_back = min(request_data.get('days_back', 30), 365)
            
            health_data = self.analytics.get_memory_health_score(days_back)
            
            return self._create_response(True, health_data)
            
        except Exception as e:
            return self._create_response(False, error=f"Health analysis failed: {str(e)}")
    
    # ===========================================
    # DASHBOARD ENDPOINTS
    # ===========================================
    
    def get_dashboard_overview(self, request_data: Dict) -> Dict:
        """
        Get comprehensive dashboard overview
        
        Expected request_data:
        {
            "include_heatmap": true,
            "include_trends": true,
            "days_back": 30
        }
        """
        try:
            if not self.dashboard:
                return self._create_response(False, error="Dashboard not available")
            
            include_heatmap = request_data.get('include_heatmap', True)
            include_trends = request_data.get('include_trends', True)
            days_back = min(request_data.get('days_back', 30), 90)
            
            overview_data = {
                'real_time_stats': self.dashboard.get_real_time_stats(),
                'system_performance': self.dashboard.get_system_performance()
            }
            
            if include_heatmap:
                overview_data['activity_heatmap'] = self.dashboard.get_activity_heatmap(days_back)
            
            if include_trends:
                overview_data['trending_topics'] = self.dashboard.get_trending_topics(7)
                overview_data['productivity_insights'] = self.dashboard.get_productivity_insights(days_back)
            
            return self._create_response(True, overview_data)
            
        except Exception as e:
            return self._create_response(False, error=f"Dashboard overview failed: {str(e)}")
    
    def get_real_time_stats(self, request_data: Dict) -> Dict:
        """Get real-time memory statistics"""
        try:
            if not self.dashboard:
                return self._create_response(False, error="Dashboard not available")
            
            stats = self.dashboard.get_real_time_stats()
            return self._create_response(True, stats)
            
        except Exception as e:
            return self._create_response(False, error=f"Real-time stats failed: {str(e)}")
    
    def get_activity_heatmap(self, request_data: Dict) -> Dict:
        """
        Get activity heatmap data
        
        Expected request_data:
        {
            "days_back": 30
        }
        """
        try:
            if not self.dashboard:
                return self._create_response(False, error="Dashboard not available")
            
            days_back = min(request_data.get('days_back', 30), 90)
            heatmap_data = self.dashboard.get_activity_heatmap(days_back)
            
            return self._create_response(True, heatmap_data)
            
        except Exception as e:
            return self._create_response(False, error=f"Activity heatmap failed: {str(e)}")
    
    # ===========================================
    # UTILITY ENDPOINTS
    # ===========================================
    
    def get_api_status(self, request_data: Dict) -> Dict:
        """Get API status and health information"""
        try:
            uptime = time.time() - self.start_time
            
            status_data = {
                'api_version': self.api_version,
                'status': 'healthy',
                'uptime_seconds': round(uptime, 2),
                'components': {
                    'search_engine': 'available' if self.search_engine else 'unavailable',
                    'analytics_engine': 'available' if self.analytics else 'unavailable',
                    'dashboard': 'available' if self.dashboard else 'unavailable',
                    'security_validator': 'available' if self.security_validator else 'unavailable'
                },
                'endpoints': [
                    'search_memories', 'get_related_memories',
                    'get_productivity_analysis', 'get_content_trends',
                    'get_knowledge_graph', 'get_memory_health',
                    'get_dashboard_overview', 'get_real_time_stats',
                    'get_activity_heatmap', 'get_api_status'
                ]
            }
            
            return self._create_response(True, status_data)
            
        except Exception as e:
            return self._create_response(False, error=f"Status check failed: {str(e)}")
    
    def clear_caches(self, request_data: Dict) -> Dict:
        """Clear all system caches"""
        try:
            cleared_caches = []
            
            if self.search_engine and hasattr(self.search_engine, 'clear_cache'):
                self.search_engine.clear_cache()
                cleared_caches.append('search_engine')
            
            if self.dashboard and hasattr(self.dashboard, 'clear_cache'):
                self.dashboard.clear_cache()
                cleared_caches.append('dashboard')
            
            return self._create_response(True, {
                'cleared_caches': cleared_caches,
                'cleared_at': int(time.time())
            }, message="Caches cleared successfully")
            
        except Exception as e:
            return self._create_response(False, error=f"Cache clearing failed: {str(e)}")
    
    # ===========================================
    # REQUEST HANDLER
    # ===========================================
    
    def handle_request(self, endpoint: str, request_data: Dict) -> Dict:
        """
        Main request handler
        
        Args:
            endpoint: API endpoint name
            request_data: Request parameters
        
        Returns:
            Standardized API response
        """
        try:
            # Map endpoints to methods
            endpoint_map = {
                'search_memories': self.search_memories,
                'get_related_memories': self.get_related_memories,
                'get_productivity_analysis': self.get_productivity_analysis,
                'get_content_trends': self.get_content_trends,
                'get_knowledge_graph': self.get_knowledge_graph,
                'get_memory_health': self.get_memory_health,
                'get_dashboard_overview': self.get_dashboard_overview,
                'get_real_time_stats': self.get_real_time_stats,
                'get_activity_heatmap': self.get_activity_heatmap,
                'get_api_status': self.get_api_status,
                'clear_caches': self.clear_caches
            }
            
            if endpoint not in endpoint_map:
                return self._create_response(False, error=f"Unknown endpoint: {endpoint}")
            
            # Execute the endpoint method
            return endpoint_map[endpoint](request_data)
            
        except Exception as e:
            # Log the full traceback for debugging
            traceback.print_exc()
            return self._create_response(False, error=f"Internal server error: {str(e)}")


# ===========================================
# STANDALONE USAGE EXAMPLE
# ===========================================

def main():
    """Example usage of the Memory API"""
    api = MemoryAPI()
    
    # Test API status
    status_response = api.handle_request('get_api_status', {})
    print("API Status:", json.dumps(status_response, indent=2))
    
    # Test search
    search_response = api.handle_request('search_memories', {
        'query': 'machine learning',
        'limit': 5
    })
    print("\\nSearch Results:", json.dumps(search_response, indent=2))
    
    # Test real-time stats
    stats_response = api.handle_request('get_real_time_stats', {})
    print("\\nReal-time Stats:", json.dumps(stats_response, indent=2))


if __name__ == "__main__":
    main()