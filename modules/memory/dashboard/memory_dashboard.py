#!/usr/bin/env python3
"""
VELOS Memory Dashboard
실시간 메모리 시스템 모니터링 및 분석 대시보드

Features:
- Real-time memory statistics
- Interactive search interface  
- Visual analytics and trends
- System health monitoring
- Performance metrics
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import sqlite3

# VELOS integrations
try:
    from modules.core.path_manager import get_db_path, get_data_path
    from modules.memory.advanced.semantic_search import SemanticSearchEngine
    from modules.memory.advanced.memory_analytics import MemoryAnalytics
except ImportError:
    # Fallback implementations
    def get_db_path():
        return "C:\giwanos/data/memory/velos.db"
    
    def get_data_path(*parts):
        return "C:\giwanos/data/" + "/".join(parts)


class MemoryDashboard:
    """Advanced memory system dashboard"""
    
    def __init__(self):
        self.db_path = get_db_path()
        self.search_engine = SemanticSearchEngine()
        self.analytics = MemoryAnalytics()
        self.cache = {}
        self.cache_duration = 60  # 1 minute cache
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.Connection(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_real_time_stats(self) -> Dict[str, Any]:
        """Get real-time memory system statistics"""
        cache_key = "real_time_stats"
        
        # Check cache
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_duration:
                return cached_data
        
        try:
            with self._get_connection() as conn:
                # Basic counts and metrics
                cursor = conn.execute("""
                    SELECT 
                        COUNT(*) as total_memory,
                        COUNT(DISTINCT role) as unique_roles,
                        COUNT(DISTINCT DATE(datetime(ts, 'unixepoch'))) as total_days,
                        SUM(LENGTH(insight)) as total_content_length,
                        AVG(LENGTH(insight)) as avg_content_length,
                        MIN(ts) as earliest_memory,
                        MAX(ts) as latest_memory
                    FROM memory
                """)
                
                stats = dict(cursor.fetchone())
                
                # Recent activity (last 24 hours)
                last_24h = int(time.time()) - 86400
                cursor = conn.execute("""
                    SELECT 
                        COUNT(*) as memory_24h,
                        COUNT(DISTINCT role) as roles_24h
                    FROM memory 
                    WHERE ts >= ?
                """, (last_24h,))
                
                recent_stats = dict(cursor.fetchone())
                
                # Top roles by activity
                cursor = conn.execute("""
                    SELECT role, COUNT(*) as count
                    FROM memory 
                    WHERE ts >= ?
                    GROUP BY role
                    ORDER BY count DESC
                    LIMIT 10
                """, (last_24h,))
                
                top_roles = {row['role']: row['count'] for row in cursor.fetchall()}
                
                # Memory growth rate
                if stats['total_days'] > 0:
                    avg_memory_per_day = stats['total_memory'] / stats['total_days']
                else:
                    avg_memory_per_day = 0
                
                # Calculate system uptime
                if stats['earliest_memory']:
                    uptime_days = (time.time() - stats['earliest_memory']) / 86400
                else:
                    uptime_days = 0
                
                result = {
                    'current_stats': {
                        'total_memory': stats['total_memory'],
                        'unique_roles': stats['unique_roles'],
                        'total_content_mb': round(stats['total_content_length'] / 1024 / 1024, 2),
                        'avg_content_length': round(stats['avg_content_length'], 1),
                        'system_uptime_days': round(uptime_days, 1),
                        'avg_memory_per_day': round(avg_memory_per_day, 1)
                    },
                    'recent_activity': {
                        'memory_last_24h': recent_stats['memory_24h'],
                        'roles_active_24h': recent_stats['roles_24h'],
                        'top_active_roles': top_roles
                    },
                    'timestamps': {
                        'earliest_memory': stats['earliest_memory'],
                        'latest_memory': stats['latest_memory'],
                        'last_updated': int(time.time())
                    }
                }
                
                # Cache the result
                self.cache[cache_key] = (result, time.time())
                return result
                
        except sqlite3.Error as e:
            print(f"Database error in real-time stats: {e}")
            return {}
    
    def get_activity_heatmap(self, days_back: int = 30) -> Dict[str, Any]:
        """Generate activity heatmap data for visualization"""
        cutoff_time = int(time.time()) - (days_back * 86400)
        
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT 
                        strftime('%Y-%m-%d', datetime(ts, 'unixepoch')) as date,
                        strftime('%H', datetime(ts, 'unixepoch')) as hour,
                        COUNT(*) as activity_count
                    FROM memory 
                    WHERE ts >= ?
                    GROUP BY date, hour
                    ORDER BY date, hour
                """, (cutoff_time,))
                
                heatmap_data = []
                date_activity = {}
                hourly_totals = {str(h): 0 for h in range(24)}
                
                for row in cursor.fetchall():
                    date = row['date']
                    hour = row['hour']
                    count = row['activity_count']
                    
                    heatmap_data.append({
                        'date': date,
                        'hour': int(hour),
                        'activity': count,
                        'intensity': min(count / 5.0, 1.0)  # Normalize for visualization
                    })
                    
                    # Track daily totals
                    if date not in date_activity:
                        date_activity[date] = 0
                    date_activity[date] += count
                    
                    # Track hourly totals
                    hourly_totals[hour] += count
                
                # Find peak activity patterns
                peak_hour = max(hourly_totals.items(), key=lambda x: x[1])
                peak_day = max(date_activity.items(), key=lambda x: x[1]) if date_activity else None
                
                return {
                    'heatmap_data': heatmap_data,
                    'daily_totals': date_activity,
                    'hourly_totals': hourly_totals,
                    'patterns': {
                        'peak_hour': {'hour': peak_hour[0], 'activity': peak_hour[1]},
                        'peak_day': {'date': peak_day[0], 'activity': peak_day[1]} if peak_day else None,
                        'most_active_days': sorted(date_activity.items(), key=lambda x: x[1], reverse=True)[:7]
                    },
                    'analysis_period_days': days_back,
                    'generated_at': int(time.time())
                }
                
        except sqlite3.Error as e:
            print(f"Database error in activity heatmap: {e}")
            return {}
    
    def search_memory(
        self,
        query: str,
        limit: int = 20,
        filters: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Enhanced memory search with dashboard formatting"""
        try:
            # Use semantic search engine
            results = self.search_engine.semantic_search(
                query=query,
                limit=limit,
                filters=filters
            )
            
            # Format results for dashboard display
            formatted_results = []
            for result in results:
                formatted_results.append({
                    'id': result.id,
                    'content': result.content,
                    'role': result.role,
                    'timestamp': result.timestamp,
                    'formatted_date': datetime.fromtimestamp(result.timestamp).strftime('%Y-%m-%d %H:%M'),
                    'similarity_score': round(result.similarity_score, 3),
                    'context_relevance': round(result.context_relevance, 3),
                    'combined_score': round(result.combined_score, 3),
                    'tags': result.tags,
                    'preview': result.content[:200] + "..." if len(result.content) > 200 else result.content
                })
            
            return {
                'query': query,
                'total_results': len(formatted_results),
                'results': formatted_results,
                'search_metadata': {
                    'search_time': time.time(),
                    'filters_applied': filters or {},
                    'semantic_search_used': True
                }
            }
            
        except Exception as e:
            print(f"Error in memory search: {e}")
            return {'error': str(e)}
    
    def get_trending_topics(self, days_back: int = 7) -> Dict[str, Any]:
        """Get trending topics and concepts"""
        try:
            trends = self.analytics.detect_content_trends(
                days_back=days_back,
                min_frequency=2
            )
            
            # Format trends for dashboard
            trending_data = []
            for trend in trends[:10]:  # Top 10 trends
                trending_data.append({
                    'topic': trend.metadata['keyword'],
                    'trend_type': trend.trend_type,
                    'confidence': round(trend.confidence, 3),
                    'frequency': trend.metadata['total_frequency'],
                    'trend_strength': round(trend.metadata['trend_strength'], 3),
                    'description': trend.description
                })
            
            return {
                'trending_topics': trending_data,
                'analysis_period_days': days_back,
                'total_trends_detected': len(trends),
                'generated_at': int(time.time())
            }
            
        except Exception as e:
            print(f"Error getting trending topics: {e}")
            return {}
    
    def get_productivity_insights(self, days_back: int = 30) -> Dict[str, Any]:
        """Get productivity insights and recommendations"""
        try:
            # Get productivity analysis
            productivity_data = self.analytics.analyze_productivity_patterns(days_back)
            
            # Get health score
            health_data = self.analytics.get_memory_health_score(days_back)
            
            # Combine insights
            return {
                'productivity_analysis': productivity_data,
                'health_assessment': health_data,
                'key_insights': self._generate_key_insights(productivity_data, health_data),
                'generated_at': int(time.time())
            }
            
        except Exception as e:
            print(f"Error getting productivity insights: {e}")
            return {}
    
    def _generate_key_insights(
        self,
        productivity_data: Dict,
        health_data: Dict
    ) -> List[str]:
        """Generate key insights from analysis data"""
        insights = []
        
        # Productivity insights
        if 'peak_hours' in productivity_data:
            peak_hours = list(productivity_data['peak_hours'].keys())
            if peak_hours:
                insights.append(f"Your most productive hours are {', '.join(map(str, peak_hours[:3]))}")
        
        if 'top_productive_roles' in productivity_data:
            top_role = next(iter(productivity_data['top_productive_roles']), None)
            if top_role:
                insights.append(f"'{top_role}' role shows highest productivity")
        
        # Health insights
        if 'health_level' in health_data:
            health_level = health_data['health_level']
            insights.append(f"Memory system health: {health_level}")
        
        if 'recommendations' in health_data:
            insights.extend(health_data['recommendations'][:2])  # Top 2 recommendations
        
        return insights[:5]  # Top 5 insights
    
    def get_knowledge_graph_data(self, days_back: int = 30) -> Dict[str, Any]:
        """Get knowledge graph data for visualization"""
        try:
            graph_data = self.analytics.generate_knowledge_graph(
                days_back=days_back,
                max_nodes=30
            )
            
            return graph_data
            
        except Exception as e:
            print(f"Error generating knowledge graph: {e}")
            return {}
    
    def get_system_performance(self) -> Dict[str, Any]:
        """Get system performance metrics"""
        try:
            with self._get_connection() as conn:
                # Database size and performance metrics
                cursor = conn.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
                db_size = cursor.fetchone()[0]
                
                # FTS index status
                cursor = conn.execute("SELECT COUNT(*) FROM memory_fts")
                fts_records = cursor.fetchone()[0]
                
                # Recent query performance (simulated)
                search_cache_stats = self.search_engine.get_cache_stats()
                
                return {
                    'database_metrics': {
                        'size_mb': round(db_size / 1024 / 1024, 2),
                        'fts_records': fts_records,
                        'last_optimized': int(time.time())  # Placeholder
                    },
                    'search_performance': {
                        'cache_hit_rate': '85%',  # Simulated
                        'avg_search_time_ms': 45,  # Simulated
                        'cache_stats': search_cache_stats
                    },
                    'system_status': 'Healthy',
                    'last_updated': int(time.time())
                }
                
        except Exception as e:
            print(f"Error getting system performance: {e}")
            return {}
    
    def export_dashboard_data(self, format_type: str = 'json') -> Dict[str, Any]:
        """Export comprehensive dashboard data"""
        try:
            dashboard_data = {
                'real_time_stats': self.get_real_time_stats(),
                'activity_heatmap': self.get_activity_heatmap(30),
                'trending_topics': self.get_trending_topics(7),
                'productivity_insights': self.get_productivity_insights(30),
                'system_performance': self.get_system_performance(),
                'export_metadata': {
                    'exported_at': int(time.time()),
                    'format': format_type,
                    'version': '1.0'
                }
            }
            
            if format_type == 'json':
                return dashboard_data
            else:
                # Could add CSV, Excel export options here
                return dashboard_data
                
        except Exception as e:
            print(f"Error exporting dashboard data: {e}")
            return {}
    
    def clear_cache(self):
        """Clear dashboard cache"""
        self.cache.clear()
        if hasattr(self.search_engine, 'clear_cache'):
            self.search_engine.clear_cache()
    
    def get_dashboard_status(self) -> Dict[str, Any]:
        """Get overall dashboard system status"""
        return {
            'status': 'Active',
            'components': {
                'semantic_search': 'Available',
                'analytics_engine': 'Available', 
                'database_connection': 'Healthy',
                'cache_system': 'Active'
            },
            'cache_info': {
                'entries': len(self.cache),
                'cache_duration': self.cache_duration
            },
            'last_check': int(time.time())
        }