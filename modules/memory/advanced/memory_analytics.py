#!/usr/bin/env python3
"""
VELOS Memory Analytics Module
메모리 패턴 분석, 트렌드 분석, 인사이트 생성

Features:
- Memory usage pattern analysis
- Content trend detection
- Knowledge graph generation
- Productivity insights
"""

import json
import sqlite3
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from collections import defaultdict, Counter
import re
import math

# Path manager integration
try:
    from modules.core.path_manager import get_db_path
except ImportError:
    def get_db_path():
        return "C:\giwanos/data/memory/velos.db"


@dataclass
class TrendInsight:
    """Trend analysis result"""
    trend_type: str
    description: str
    confidence: float
    data_points: List[Tuple[int, float]]
    metadata: Dict[str, Any]


@dataclass
class KnowledgeNode:
    """Knowledge graph node"""
    concept: str
    frequency: int
    connections: List[str]
    importance_score: float
    related_memory: List[int]


class MemoryAnalytics:
    """Advanced memory analytics and pattern detection"""
    
    def __init__(self):
        self.db_path = get_db_path()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn
    
    def analyze_productivity_patterns(
        self,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze productivity patterns from memory data
        
        Returns insights about:
        - Peak productivity hours
        - Most productive roles/activities
        - Productivity trends over time
        - Knowledge accumulation rate
        """
        cutoff_time = int(time.time()) - (days_back * 86400)
        
        try:
            with self._get_connection() as conn:
                # Hourly activity analysis
                cursor = conn.execute("""
                    SELECT 
                        strftime('%H', datetime(ts, 'unixepoch')) as hour,
                        strftime('%w', datetime(ts, 'unixepoch')) as weekday,
                        COUNT(*) as memory_count,
                        AVG(LENGTH(insight)) as avg_length,
                        role
                    FROM memory 
                    WHERE ts >= ?
                    GROUP BY hour, weekday, role
                    ORDER BY hour, weekday
                """, (cutoff_time,))
                
                hourly_data = defaultdict(lambda: defaultdict(list))
                role_productivity = defaultdict(lambda: defaultdict(int))
                
                for row in cursor.fetchall():
                    hour = int(row['hour'])
                    weekday = int(row['weekday'])
                    role = row['role']
                    count = row['memory_count']
                    avg_len = row['avg_length']
                    
                    productivity_score = count * (avg_len / 100)  # Normalize length
                    
                    hourly_data[hour][weekday].append(productivity_score)
                    role_productivity[role][hour] += productivity_score
                
                # Find peak hours
                peak_hours = {}
                for hour in range(24):
                    scores = []
                    for weekday in range(7):
                        if weekday in hourly_data[hour]:
                            scores.extend(hourly_data[hour][weekday])
                    
                    if scores:
                        peak_hours[hour] = {
                            'avg_productivity': sum(scores) / len(scores),
                            'total_activities': len(scores)
                        }
                
                # Daily trend analysis
                cursor = conn.execute("""
                    SELECT 
                        DATE(datetime(ts, 'unixepoch')) as date,
                        COUNT(*) as memory_count,
                        COUNT(DISTINCT role) as unique_roles,
                        SUM(LENGTH(insight)) as total_content
                    FROM memory 
                    WHERE ts >= ?
                    GROUP BY date
                    ORDER BY date
                """, (cutoff_time,))
                
                daily_trends = []
                for row in cursor.fetchall():
                    daily_trends.append({
                        'date': row['date'],
                        'memory_count': row['memory_count'],
                        'unique_roles': row['unique_roles'],
                        'content_volume': row['total_content'],
                        'productivity_index': row['memory_count'] * row['unique_roles']
                    })
                
                # Most productive roles
                top_roles = sorted(
                    [(role, sum(hourly_scores.values())) 
                     for role, hourly_scores in role_productivity.items()],
                    key=lambda x: x[1], reverse=True
                )[:10]
                
                return {
                    'analysis_period_days': days_back,
                    'peak_hours': dict(sorted(peak_hours.items(), 
                                            key=lambda x: x[1]['avg_productivity'], reverse=True)[:5]),
                    'daily_trends': daily_trends,
                    'top_productive_roles': dict(top_roles),
                    'overall_stats': {
                        'total_peak_hours': len([h for h, data in peak_hours.items() 
                                               if data['avg_productivity'] > 5]),
                        'most_consistent_hours': self._find_consistent_hours(hourly_data),
                        'productivity_variance': self._calculate_productivity_variance(daily_trends)
                    },
                    'generated_at': int(time.time())
                }
                
        except sqlite3.Error as e:
            print(f"Database error in productivity analysis: {e}")
            return {}
    
    def _find_consistent_hours(self, hourly_data: Dict) -> List[int]:
        """Find hours with consistent activity across weekdays"""
        consistent_hours = []
        
        for hour in range(24):
            weekday_scores = []
            for weekday in range(7):
                if weekday in hourly_data[hour] and hourly_data[hour][weekday]:
                    avg_score = sum(hourly_data[hour][weekday]) / len(hourly_data[hour][weekday])
                    weekday_scores.append(avg_score)
            
            if len(weekday_scores) >= 5:  # At least 5 weekdays with data
                variance = self._calculate_variance(weekday_scores)
                if variance < 2.0:  # Low variance = consistent
                    consistent_hours.append(hour)
        
        return consistent_hours
    
    def _calculate_productivity_variance(self, daily_trends: List[Dict]) -> float:
        """Calculate variance in daily productivity"""
        if len(daily_trends) < 2:
            return 0.0
        
        productivity_scores = [trend['productivity_index'] for trend in daily_trends]
        return self._calculate_variance(productivity_scores)
    
    def _calculate_variance(self, values: List[float]) -> float:
        """Calculate variance of values"""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance
    
    def detect_content_trends(
        self,
        days_back: int = 30,
        min_frequency: int = 3
    ) -> List[TrendInsight]:
        """
        Detect trending topics and concepts in memory content
        
        Args:
            days_back: Number of days to analyze
            min_frequency: Minimum frequency for trend detection
        
        Returns:
            List of trend insights
        """
        cutoff_time = int(time.time()) - (days_back * 86400)
        trends = []
        
        try:
            with self._get_connection() as conn:
                # Get all memory in the period
                cursor = conn.execute("""
                    SELECT ts, insight, role, tags
                    FROM memory 
                    WHERE ts >= ?
                    ORDER BY ts
                """, (cutoff_time,))
                
                memory = cursor.fetchall()
                
                # Extract keywords and track their frequency over time
                keyword_timeline = defaultdict(lambda: defaultdict(int))
                
                for memory in memory:
                    # Simple keyword extraction
                    text = memory['insight'].lower()
                    words = re.findall(r'\b\w{4,}\b', text)  # Words with 4+ characters
                    
                    # Group by week for trend analysis
                    week = (memory['ts'] - cutoff_time) // 604800  # Week number
                    
                    # Count word frequencies
                    for word in words:
                        if word not in ['this', 'that', 'with', 'from', 'they', 'have', 'will']:
                            keyword_timeline[word][week] += 1
                
                # Analyze trends for each keyword
                for keyword, weekly_counts in keyword_timeline.items():
                    total_count = sum(weekly_counts.values())
                    if total_count < min_frequency:
                        continue
                    
                    # Calculate trend direction and confidence
                    weeks = sorted(weekly_counts.keys())
                    if len(weeks) < 2:
                        continue
                    
                    # Simple linear trend calculation
                    trend_direction, confidence = self._calculate_trend(
                        [(week, weekly_counts[week]) for week in weeks]
                    )
                    
                    if confidence > 0.3:  # Minimum confidence threshold
                        trend_type = "increasing" if trend_direction > 0 else "decreasing"
                        
                        trends.append(TrendInsight(
                            trend_type=trend_type,
                            description=f"Keyword '{keyword}' showing {trend_type} trend",
                            confidence=confidence,
                            data_points=[(week, weekly_counts[week]) for week in weeks],
                            metadata={
                                'keyword': keyword,
                                'total_frequency': total_count,
                                'trend_strength': abs(trend_direction),
                                'weeks_analyzed': len(weeks)
                            }
                        ))
                
                # Sort by confidence and return top trends
                trends.sort(key=lambda x: x.confidence, reverse=True)
                return trends[:20]  # Top 20 trends
                
        except sqlite3.Error as e:
            print(f"Database error in trend detection: {e}")
            return []
    
    def _calculate_trend(self, data_points: List[Tuple[int, int]]) -> Tuple[float, float]:
        """Calculate linear trend direction and confidence"""
        if len(data_points) < 2:
            return 0.0, 0.0
        
        n = len(data_points)
        sum_x = sum(x for x, y in data_points)
        sum_y = sum(y for x, y in data_points)
        sum_xy = sum(x * y for x, y in data_points)
        sum_x2 = sum(x * x for x, y in data_points)
        
        # Linear regression slope
        denominator = n * sum_x2 - sum_x * sum_x
        if denominator == 0:
            return 0.0, 0.0
        
        slope = (n * sum_xy - sum_x * sum_y) / denominator
        
        # Calculate R-squared for confidence
        mean_y = sum_y / n
        ss_tot = sum((y - mean_y) ** 2 for x, y in data_points)
        
        if ss_tot == 0:
            confidence = 1.0 if slope == 0 else 0.0
        else:
            # Predicted values
            intercept = (sum_y - slope * sum_x) / n
            predicted = [slope * x + intercept for x, y in data_points]
            ss_res = sum((data_points[i][1] - predicted[i]) ** 2 for i in range(n))
            confidence = 1 - (ss_res / ss_tot)
        
        return slope, max(0.0, confidence)
    
    def generate_knowledge_graph(
        self,
        days_back: int = 30,
        max_nodes: int = 50
    ) -> Dict[str, Any]:
        """
        Generate a knowledge graph from memory content
        
        Args:
            days_back: Number of days to analyze
            max_nodes: Maximum number of nodes in the graph
        
        Returns:
            Knowledge graph data structure
        """
        cutoff_time = int(time.time()) - (days_back * 86400)
        
        try:
            with self._get_connection() as conn:
                # Get memory and extract concepts
                cursor = conn.execute("""
                    SELECT id, insight, role, tags
                    FROM memory 
                    WHERE ts >= ?
                """, (cutoff_time,))
                
                memory = cursor.fetchall()
                
                # Extract concepts (important keywords/phrases)
                concept_frequency = Counter()
                concept_cooccurrence = defaultdict(lambda: defaultdict(int))
                concept_memory = defaultdict(list)
                
                for memory in memory:
                    text = memory['insight'].lower()
                    # Extract meaningful concepts (simplified)
                    concepts = self._extract_concepts(text)
                    
                    for concept in concepts:
                        concept_frequency[concept] += 1
                        concept_memory[concept].append(memory['id'])
                    
                    # Track co-occurrences
                    for i, concept1 in enumerate(concepts):
                        for concept2 in concepts[i+1:]:
                            concept_cooccurrence[concept1][concept2] += 1
                            concept_cooccurrence[concept2][concept1] += 1
                
                # Select top concepts
                top_concepts = [concept for concept, freq in concept_frequency.most_common(max_nodes)]
                
                # Build knowledge nodes
                nodes = []
                edges = []
                
                for concept in top_concepts:
                    # Calculate importance score
                    frequency = concept_frequency[concept]
                    connections = list(concept_cooccurrence[concept].keys())
                    
                    importance = frequency * (1 + len(connections) * 0.1)
                    
                    node = KnowledgeNode(
                        concept=concept,
                        frequency=frequency,
                        connections=connections[:10],  # Top 10 connections
                        importance_score=importance,
                        related_memory=concept_memory[concept][:5]  # Top 5 related memory
                    )
                    
                    nodes.append(node)
                
                # Build edges (relationships)
                for concept1 in top_concepts:
                    for concept2, weight in concept_cooccurrence[concept1].items():
                        if concept2 in top_concepts and weight > 1:  # Minimum connection strength
                            edges.append({
                                'from': concept1,
                                'to': concept2,
                                'weight': weight,
                                'strength': min(weight / 5.0, 1.0)  # Normalized strength
                            })
                
                # Calculate graph metrics
                total_nodes = len(nodes)
                total_edges = len(edges)
                avg_connections = sum(len(node.connections) for node in nodes) / max(total_nodes, 1)
                
                return {
                    'nodes': [
                        {
                            'id': node.concept,
                            'label': node.concept,
                            'frequency': node.frequency,
                            'importance': node.importance_score,
                            'connections': len(node.connections),
                            'related_memory': node.related_memory
                        }
                        for node in nodes
                    ],
                    'edges': edges,
                    'metrics': {
                        'total_nodes': total_nodes,
                        'total_edges': total_edges,
                        'average_connections': avg_connections,
                        'graph_density': (total_edges * 2) / max(total_nodes * (total_nodes - 1), 1)
                    },
                    'analysis_period_days': days_back,
                    'generated_at': int(time.time())
                }
                
        except sqlite3.Error as e:
            print(f"Database error in knowledge graph generation: {e}")
            return {}
    
    def _extract_concepts(self, text: str) -> List[str]:
        """Extract meaningful concepts from text"""
        # Simple concept extraction - can be enhanced with NLP
        concepts = []
        
        # Extract meaningful words (4+ characters, not common words)
        stop_words = {
            'this', 'that', 'with', 'from', 'they', 'have', 'will', 'been', 'were',
            'are', 'was', 'the', 'and', 'for', 'you', 'not', 'but', 'can', 'all',
            'any', 'had', 'her', 'him', 'his', 'how', 'its', 'may', 'new', 'now',
            'old', 'see', 'two', 'way', 'who', 'boy', 'did', 'has', 'let', 'put',
            'say', 'she', 'too', 'use'
        }
        
        words = re.findall(r'\b[a-z]{4,}\b', text)
        concepts.extend([word for word in words if word not in stop_words])
        
        # Extract simple phrases (2-3 words)
        phrases = re.findall(r'\b[a-z]+\s+[a-z]+\b', text)
        concepts.extend([phrase for phrase in phrases if len(phrase) > 6])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_concepts = []
        for concept in concepts:
            if concept not in seen:
                seen.add(concept)
                unique_concepts.append(concept)
        
        return unique_concepts[:20]  # Limit concepts per text
    
    def get_memory_health_score(self, days_back: int = 30) -> Dict[str, Any]:
        """
        Calculate overall memory system health score
        
        Factors:
        - Activity consistency
        - Content diversity
        - Knowledge accumulation rate
        - System utilization
        """
        cutoff_time = int(time.time()) - (days_back * 86400)
        
        try:
            with self._get_connection() as conn:
                # Basic metrics
                cursor = conn.execute("""
                    SELECT 
                        COUNT(*) as total_memory,
                        COUNT(DISTINCT role) as unique_roles,
                        COUNT(DISTINCT DATE(datetime(ts, 'unixepoch'))) as active_days,
                        AVG(LENGTH(insight)) as avg_content_length,
                        MIN(ts) as earliest_memory,
                        MAX(ts) as latest_memory
                    FROM memory 
                    WHERE ts >= ?
                """, (cutoff_time,))
                
                stats = dict(cursor.fetchone())
                
                # Calculate health components
                activity_score = min(stats['total_memory'] / (days_back * 5), 1.0)  # Target: 5 memory/day
                consistency_score = stats['active_days'] / days_back  # Daily activity consistency
                diversity_score = min(stats['unique_roles'] / 10, 1.0)  # Role diversity
                content_quality_score = min(stats['avg_content_length'] / 200, 1.0)  # Content depth
                
                # Overall health score (weighted average)
                health_score = (
                    activity_score * 0.3 +
                    consistency_score * 0.25 +
                    diversity_score * 0.2 +
                    content_quality_score * 0.25
                )
                
                # Health level classification
                if health_score >= 0.8:
                    health_level = "Excellent"
                elif health_score >= 0.6:
                    health_level = "Good"
                elif health_score >= 0.4:
                    health_level = "Fair"
                else:
                    health_level = "Needs Attention"
                
                return {
                    'health_score': round(health_score, 3),
                    'health_level': health_level,
                    'components': {
                        'activity_score': round(activity_score, 3),
                        'consistency_score': round(consistency_score, 3),
                        'diversity_score': round(diversity_score, 3),
                        'content_quality_score': round(content_quality_score, 3)
                    },
                    'raw_stats': stats,
                    'recommendations': self._generate_health_recommendations(
                        activity_score, consistency_score, diversity_score, content_quality_score
                    ),
                    'analysis_period_days': days_back,
                    'generated_at': int(time.time())
                }
                
        except sqlite3.Error as e:
            print(f"Database error in health score calculation: {e}")
            return {}
    
    def _generate_health_recommendations(
        self, activity: float, consistency: float, diversity: float, quality: float
    ) -> List[str]:
        """Generate personalized recommendations based on health scores"""
        recommendations = []
        
        if activity < 0.5:
            recommendations.append("Consider increasing daily memory recording activity")
        
        if consistency < 0.4:
            recommendations.append("Try to maintain more consistent daily usage")
        
        if diversity < 0.3:
            recommendations.append("Explore using different roles/contexts for varied perspectives")
        
        if quality < 0.4:
            recommendations.append("Focus on writing more detailed and comprehensive insights")
        
        if not recommendations:
            recommendations.append("Excellent memory system health! Keep up the good work.")
        
        return recommendations