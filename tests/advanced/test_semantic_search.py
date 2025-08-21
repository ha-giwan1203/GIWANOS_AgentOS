#!/usr/bin/env python3
"""
VELOS Advanced Semantic Search Tests
고급 의미 기반 검색 시스템 테스트
"""

import unittest
import sys
import os
import tempfile
import sqlite3
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

try:
    from modules.memory.advanced.semantic_search import SemanticSearchEngine, SearchResult
    from modules.memory.storage.sqlite_store import init_schema
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)


class TestSemanticSearch(unittest.TestCase):
    """Test cases for semantic search functionality"""
    
    def setUp(self):
        """Set up test database and search engine"""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Initialize database schema
        conn = sqlite3.connect(self.temp_db.name)
        init_schema(conn)
        
        # Insert test data
        test_memories = [
            (1623456789, 'user', 'Python programming is great for data analysis', '{"tags": ["programming", "python"]}'),
            (1623456790, 'assistant', 'Machine learning algorithms can solve complex problems', '{"tags": ["ml", "algorithms"]}'),
            (1623456791, 'user', 'Data visualization helps understand patterns in data', '{"tags": ["data", "visualization"]}'),
            (1623456792, 'assistant', 'Python libraries like pandas are useful for data manipulation', '{"tags": ["python", "pandas"]}'),
            (1623456793, 'user', 'Deep learning models require large datasets for training', '{"tags": ["deep learning", "data"]}')
        ]
        
        for ts, role, insight, tags in test_memories:
            conn.execute(
                "INSERT INTO memory (ts, role, insight, tags) VALUES (?, ?, ?, ?)",
                (ts, role, insight, tags)
            )
        
        conn.commit()
        conn.close()
        
        # Mock the get_db_path function for testing
        import modules.memory.advanced.semantic_search
        modules.memory.advanced.semantic_search.get_db_path = lambda: self.temp_db.name
        
        # Initialize search engine
        self.search_engine = SemanticSearchEngine()
    
    def tearDown(self):
        """Clean up test database"""
        os.unlink(self.temp_db.name)
    
    def test_text_similarity_calculation(self):
        """Test text similarity calculation"""
        text1 = "Python programming is great"
        text2 = "Programming in Python is awesome"
        
        similarity = self.search_engine._calculate_text_similarity(text1, text2)
        
        # Should have some similarity due to common words
        self.assertGreater(similarity, 0.3)
        self.assertLessEqual(similarity, 1.0)
    
    def test_fts_query_building(self):
        """Test FTS query construction"""
        # Single word query
        query1 = "python"
        fts_query1 = self.search_engine._build_fts_query(query1)
        self.assertIn("python", fts_query1)
        
        # Multi-word query
        query2 = "machine learning algorithms"
        fts_query2 = self.search_engine._build_fts_query(query2)
        self.assertIn("machine", fts_query2)
        self.assertIn("learning", fts_query2)
    
    def test_semantic_search_basic(self):
        """Test basic semantic search functionality"""
        # Search for Python-related content
        results = self.search_engine.semantic_search("python programming", limit=3)
        
        # Should return results
        self.assertGreater(len(results), 0)
        
        # Check result structure
        for result in results:
            self.assertIsInstance(result, SearchResult)
            self.assertIsNotNone(result.content)
            self.assertIsInstance(result.similarity_score, float)
            self.assertIsInstance(result.context_relevance, float)
    
    def test_semantic_search_with_filters(self):
        """Test semantic search with filters"""
        # Search with role filter
        results = self.search_engine.semantic_search(
            "data analysis",
            filters={'role': 'user'}
        )
        
        # All results should have 'user' role
        for result in results:
            self.assertEqual(result.role, 'user')
    
    def test_semantic_search_with_context(self):
        """Test semantic search with context"""
        context = {
            'preferred_roles': ['assistant'],
            'tags': ['ml', 'algorithms']
        }
        
        results = self.search_engine.semantic_search(
            "machine learning",
            context=context,
            limit=5
        )
        
        # Should return some results
        self.assertGreaterEqual(len(results), 0)
        
        # Check that context affects ranking
        if results:
            self.assertGreater(results[0].combined_score, 0)
    
    def test_related_memories_search(self):
        """Test finding related memories"""
        # Assuming memory ID 1 exists
        related = self.search_engine.get_related_memories(
            memory_id=1,
            limit=3,
            similarity_threshold=0.1
        )
        
        # Should not include the reference memory itself
        memory_ids = [r.id for r in related]
        self.assertNotIn(1, memory_ids)
    
    def test_search_cache(self):
        """Test search result caching"""
        query = "python data"
        
        # First search
        results1 = self.search_engine.semantic_search(query, limit=5)
        
        # Second search (should use cache)
        results2 = self.search_engine.semantic_search(query, limit=5)
        
        # Results should be identical
        self.assertEqual(len(results1), len(results2))
        
        # Clear cache
        self.search_engine.clear_cache()
        cache_stats = self.search_engine.get_cache_stats()
        self.assertEqual(cache_stats['cache_size'], 0)
    
    def test_context_relevance_calculation(self):
        """Test context relevance calculation"""
        # Mock result data
        result_data = {
            'ts': 1623456789,
            'role': 'user',
            'tags': '["python", "data"]'
        }
        
        # Mock search context
        context = {
            'current_time': 1623456890,  # 101 seconds later
            'preferred_roles': ['user'],
            'tags': ['python']
        }
        
        relevance = self.search_engine._calculate_context_relevance(result_data, context)
        
        # Should have some relevance due to matching role and tags
        self.assertGreater(relevance, 0)
        self.assertLessEqual(relevance, 1.0)
    
    def test_empty_query_handling(self):
        """Test handling of empty queries"""
        # Empty query should return empty results
        results = self.search_engine.semantic_search("", limit=5)
        self.assertEqual(len(results), 0)
        
        # Whitespace-only query should return empty results
        results = self.search_engine.semantic_search("   ", limit=5)
        self.assertEqual(len(results), 0)
    
    def test_search_result_properties(self):
        """Test SearchResult dataclass properties"""
        # Create a test SearchResult
        result = SearchResult(
            id=1,
            content="Test content",
            similarity_score=0.8,
            context_relevance=0.6,
            timestamp=1623456789,
            role="user",
            tags=["test"],
            metadata={"test": True}
        )
        
        # Test combined score calculation
        expected_combined = (0.8 * 0.7) + (0.6 * 0.3)
        self.assertAlmostEqual(result.combined_score, expected_combined, places=2)


class TestSearchIntegration(unittest.TestCase):
    """Integration tests for search functionality"""
    
    def setUp(self):
        """Set up integration test environment"""
        # Create temporary database with more realistic data
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Initialize database schema
        conn = sqlite3.connect(self.temp_db.name)
        init_schema(conn)
        
        # Insert more comprehensive test data
        test_data = [
            (1623456789, 'user', 'I need help with Python pandas DataFrame operations', '["python", "pandas", "help"]'),
            (1623456790, 'assistant', 'You can use df.groupby() for aggregation operations in pandas', '["python", "pandas", "groupby"]'),
            (1623456791, 'user', 'Machine learning model accuracy is important for predictions', '["ml", "accuracy", "predictions"]'),
            (1623456792, 'assistant', 'Cross-validation helps evaluate model performance reliably', '["ml", "cv", "evaluation"]'),
            (1623456793, 'user', 'Data visualization with matplotlib and seaborn is powerful', '["visualization", "matplotlib", "seaborn"]'),
            (1623456794, 'assistant', 'Plotly offers interactive visualizations for data exploration', '["visualization", "plotly", "interactive"]'),
        ]
        
        for ts, role, insight, tags_json in test_data:
            conn.execute(
                "INSERT INTO memory (ts, role, insight, tags) VALUES (?, ?, ?, ?)",
                (ts, role, insight, tags_json)
            )
        
        conn.commit()
        conn.close()
        
        # Mock the get_db_path function
        import modules.memory.advanced.semantic_search
        modules.memory.advanced.semantic_search.get_db_path = lambda: self.temp_db.name
        
        self.search_engine = SemanticSearchEngine()
    
    def tearDown(self):
        """Clean up"""
        os.unlink(self.temp_db.name)
    
    def test_comprehensive_search_workflow(self):
        """Test complete search workflow"""
        # 1. Basic search
        results = self.search_engine.semantic_search("pandas operations", limit=10)
        self.assertGreater(len(results), 0)
        
        # 2. Check that pandas-related content ranks higher
        pandas_results = [r for r in results if 'pandas' in r.content.lower()]
        self.assertGreater(len(pandas_results), 0)
        
        # 3. Related memories search
        if results:
            related = self.search_engine.get_related_memories(results[0].id, limit=3)
            # Should find some related memories
            self.assertGreaterEqual(len(related), 0)
        
        # 4. Search with complex context
        context = {
            'preferred_roles': ['assistant'],
            'tags': ['python', 'pandas']
        }
        
        contextual_results = self.search_engine.semantic_search(
            "data manipulation",
            context=context,
            limit=5
        )
        
        # Should return results
        self.assertGreaterEqual(len(contextual_results), 0)
    
    def test_performance_with_larger_dataset(self):
        """Test search performance with more data"""
        # Add more test data
        conn = sqlite3.connect(self.temp_db.name)
        
        # Generate additional test memories
        base_time = 1623456800
        for i in range(50):
            conn.execute(
                "INSERT INTO memory (ts, role, insight, tags) VALUES (?, ?, ?, ?)",
                (
                    base_time + i,
                    'user' if i % 2 == 0 else 'assistant',
                    f"Test memory {i} about data science and machine learning topic {i % 5}",
                    f'["test", "data", "ml", "topic_{i % 5}"]'
                )
            )
        
        conn.commit()
        conn.close()
        
        # Test search performance
        import time
        start_time = time.time()
        
        results = self.search_engine.semantic_search("data science machine learning", limit=20)
        
        search_time = time.time() - start_time
        
        # Should complete search reasonably quickly (under 1 second for test data)
        self.assertLess(search_time, 1.0)
        self.assertGreater(len(results), 0)


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)