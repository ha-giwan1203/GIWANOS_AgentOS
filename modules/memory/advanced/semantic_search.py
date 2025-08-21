#!/usr/bin/env python3
"""
VELOS Advanced Semantic Search Module
고급 의미 기반 검색 및 분석 시스템

Features:
- Semantic similarity search
- Context-aware retrieval
- Multi-modal search capabilities
- Advanced ranking algorithms
"""

import json
import math
import re
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from dataclasses import dataclass
from collections import defaultdict
import sqlite3
import time

# Path manager integration (Phase 2 compatibility)
try:
    from modules.core.path_manager import get_db_path, get_data_path
    from modules.core.security_validator import VelosSecurityValidator
except ImportError:
    def get_db_path():
        return "/home/user/webapp/data/memory/velos.db"
    
    def get_data_path(*parts):
        return os.path.join("/home/user/webapp", "data", *parts)
    
    class VelosSecurityValidator:
        def validate_search_query(self, query: str) -> bool:
            return True


@dataclass
class SearchResult:
    """Enhanced search result with metadata"""
    id: int
    content: str
    similarity_score: float
    context_relevance: float
    timestamp: int
    role: str
    tags: List[str]
    metadata: Dict[str, Any]
    
    @property
    def combined_score(self) -> float:
        """Combined relevance score"""
        return (self.similarity_score * 0.7) + (self.context_relevance * 0.3)


class SemanticSearchEngine:
    """Advanced semantic search engine for VELOS memory"""
    
    def __init__(self):
        self.db_path = get_db_path()
        self.security_validator = VelosSecurityValidator()
        self.search_cache = {}
        self.cache_ttl = 300  # 5 minutes
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with optimizations"""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        
        # Performance optimizations
        conn.execute("PRAGMA cache_size = 10000")
        conn.execute("PRAGMA temp_store = MEMORY")
        conn.execute("PRAGMA synchronous = NORMAL")
        
        return conn
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between texts using TF-IDF approach"""
        # Simple but effective similarity calculation
        words1 = set(re.findall(r'\w+', text1.lower()))
        words2 = set(re.findall(r'\w+', text2.lower()))
        
        if not words1 or not words2:
            return 0.0
        
        # Jaccard similarity with length normalization
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        jaccard = intersection / union if union > 0 else 0.0
        
        # Length penalty for very short/long texts
        len_factor = min(len(text1), len(text2)) / max(len(text1), len(text2), 1)
        
        return jaccard * math.sqrt(len_factor)
    
    def _calculate_context_relevance(self, result: Dict, search_context: Dict) -> float:
        """Calculate context relevance based on temporal and role factors"""
        relevance = 0.0
        
        # Temporal relevance (more recent = more relevant)
        if 'timestamp' in result and 'current_time' in search_context:
            time_diff = search_context['current_time'] - result['ts']
            if time_diff < 86400:  # Last 24 hours
                relevance += 0.3
            elif time_diff < 604800:  # Last week
                relevance += 0.2
            elif time_diff < 2592000:  # Last month
                relevance += 0.1
        
        # Role relevance
        if 'preferred_roles' in search_context and result.get('role'):
            if result['role'] in search_context['preferred_roles']:
                relevance += 0.3
        
        # Tag relevance
        if 'tags' in search_context and result.get('tags'):
            result_tags = json.loads(result.get('tags', '[]'))
            common_tags = set(search_context['tags']) & set(result_tags)
            if common_tags:
                relevance += 0.2 * (len(common_tags) / len(search_context['tags']))
        
        return min(relevance, 1.0)
    
    def semantic_search(
        self,
        query: str,
        limit: int = 20,
        context: Optional[Dict] = None,
        filters: Optional[Dict] = None
    ) -> List[SearchResult]:
        """
        Advanced semantic search with context awareness
        
        Args:
            query: Search query string
            limit: Maximum number of results
            context: Search context (current time, preferred roles, tags, etc.)
            filters: Additional filters (role, date range, etc.)
        
        Returns:
            List of enhanced search results
        """
        # Security validation
        if not self.security_validator.validate_search_query(query):
            return []
        
        # Check cache
        cache_key = f"{query}:{limit}:{hash(str(context))}"
        if cache_key in self.search_cache:
            cached_result, cached_time = self.search_cache[cache_key]
            if time.time() - cached_time < self.cache_ttl:
                return cached_result
        
        # Set up search context
        search_context = context or {}
        search_context['current_time'] = int(time.time())
        
        results = []
        
        try:
            with self._get_connection() as conn:
                # Build FTS query for initial filtering
                fts_query = self._build_fts_query(query)
                
                # Base SQL with FTS
                sql = """
                    SELECT m.id, m.ts, m.role, m.insight, m.raw, m.tags,
                           bm25(memory_fts) as fts_score
                    FROM memory m
                    JOIN memory_fts ON m.rowid = memory_fts.rowid
                    WHERE memory_fts MATCH ?
                """
                
                params = [fts_query]
                
                # Add filters
                if filters:
                    if 'role' in filters:
                        sql += " AND m.role = ?"
                        params.append(filters['role'])
                    
                    if 'date_from' in filters:
                        sql += " AND m.ts >= ?"
                        params.append(filters['date_from'])
                    
                    if 'date_to' in filters:
                        sql += " AND m.ts <= ?"
                        params.append(filters['date_to'])
                
                sql += " ORDER BY fts_score DESC LIMIT ?"
                params.append(limit * 2)  # Get more for re-ranking
                
                cursor = conn.execute(sql, params)
                rows = cursor.fetchall()
                
                # Process and rank results
                for row in rows:
                    # Calculate semantic similarity
                    content = row['insight']
                    similarity = self._calculate_text_similarity(query, content)
                    
                    # Calculate context relevance
                    context_relevance = self._calculate_context_relevance(dict(row), search_context)
                    
                    # Parse tags
                    try:
                        tags = json.loads(row['tags']) if row['tags'] else []
                    except:
                        tags = []
                    
                    # Create enhanced result
                    result = SearchResult(
                        id=row['id'],
                        content=content,
                        similarity_score=similarity,
                        context_relevance=context_relevance,
                        timestamp=row['ts'],
                        role=row['role'],
                        tags=tags,
                        metadata={
                            'fts_score': row['fts_score'],
                            'raw_content': row['raw'],
                        }
                    )
                    
                    results.append(result)
                
                # Sort by combined score and limit
                results.sort(key=lambda x: x.combined_score, reverse=True)
                results = results[:limit]
                
                # Cache results
                self.search_cache[cache_key] = (results, time.time())
                
        except sqlite3.Error as e:
            print(f"Database error in semantic search: {e}")
            return []
        
        return results
    
    def _build_fts_query(self, query: str) -> str:
        """Build optimized FTS query from natural language query"""
        # Clean and tokenize
        words = re.findall(r'\w+', query.lower())
        
        if not words:
            return '""'
        
        # Build query with different strategies
        if len(words) == 1:
            # Single word: exact match or prefix
            return f'"{words[0]}" OR {words[0]}*'
        
        elif len(words) <= 3:
            # Short phrases: try exact phrase and individual words
            phrase = ' '.join(words)
            individual = ' OR '.join([f'{word}*' for word in words])
            return f'"{phrase}" OR ({individual})'
        
        else:
            # Longer queries: use NEAR and individual terms
            phrase = ' '.join(words[:4])  # First 4 words as phrase
            important_words = [word for word in words if len(word) > 3][:5]
            near_terms = f"NEAR({' '.join(important_words[:3])})" if len(important_words) >= 3 else ''
            individual = ' OR '.join([f'{word}*' for word in important_words])
            
            parts = [f'"{phrase}"']
            if near_terms:
                parts.append(near_terms)
            if individual:
                parts.append(f'({individual})')
            
            return ' OR '.join(parts)
    
    def get_related_memories(
        self,
        memory_id: int,
        limit: int = 10,
        similarity_threshold: float = 0.3
    ) -> List[SearchResult]:
        """Find memories related to a specific memory"""
        try:
            with self._get_connection() as conn:
                # Get the reference memory
                cursor = conn.execute(
                    "SELECT insight, role, tags FROM memory WHERE id = ?",
                    (memory_id,)
                )
                ref_memory = cursor.fetchone()
                
                if not ref_memory:
                    return []
                
                # Use the insight as query
                query = ref_memory['insight']
                context = {
                    'preferred_roles': [ref_memory['role']],
                    'tags': json.loads(ref_memory['tags']) if ref_memory['tags'] else []
                }
                
                # Search for similar memories (excluding the reference)
                results = self.semantic_search(query, limit + 1, context)
                
                # Remove the reference memory and apply threshold
                filtered_results = [
                    r for r in results 
                    if r.id != memory_id and r.similarity_score >= similarity_threshold
                ]
                
                return filtered_results[:limit]
                
        except sqlite3.Error as e:
            print(f"Database error in related memories search: {e}")
            return []
    
    def analyze_search_patterns(self, days_back: int = 30) -> Dict[str, Any]:
        """Analyze search patterns and memory usage"""
        cutoff_time = int(time.time()) - (days_back * 86400)
        
        try:
            with self._get_connection() as conn:
                # Basic statistics
                cursor = conn.execute(
                    """
                    SELECT 
                        COUNT(*) as total_memories,
                        COUNT(DISTINCT role) as unique_roles,
                        AVG(LENGTH(insight)) as avg_content_length
                    FROM memory 
                    WHERE ts >= ?
                    """,
                    (cutoff_time,)
                )
                stats = dict(cursor.fetchone())
                
                # Role distribution
                cursor = conn.execute(
                    """
                    SELECT role, COUNT(*) as count 
                    FROM memory 
                    WHERE ts >= ? 
                    GROUP BY role 
                    ORDER BY count DESC
                    """,
                    (cutoff_time,)
                )
                role_stats = {row['role']: row['count'] for row in cursor.fetchall()}
                
                # Temporal patterns
                cursor = conn.execute(
                    """
                    SELECT 
                        strftime('%H', datetime(ts, 'unixepoch')) as hour,
                        COUNT(*) as count
                    FROM memory 
                    WHERE ts >= ?
                    GROUP BY hour
                    ORDER BY hour
                    """,
                    (cutoff_time,)
                )
                hourly_stats = {row['hour']: row['count'] for row in cursor.fetchall()}
                
                return {
                    'period_days': days_back,
                    'basic_stats': stats,
                    'role_distribution': role_stats,
                    'hourly_activity': hourly_stats,
                    'analysis_timestamp': int(time.time())
                }
                
        except sqlite3.Error as e:
            print(f"Database error in pattern analysis: {e}")
            return {}
    
    def clear_cache(self):
        """Clear search cache"""
        self.search_cache.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            'cache_size': len(self.search_cache),
            'cache_ttl': self.cache_ttl,
            'memory_usage_estimate': len(str(self.search_cache)) * 8  # Rough estimate
        }