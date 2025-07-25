
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import time

class EnhancedSemanticCache:
    def __init__(self, threshold=0.9, max_cache_size=100):
        self.cache = []
        self.threshold = threshold
        self.max_cache_size = max_cache_size

    def add_to_cache(self, query_vec, response):
        timestamp = time.time()
        self.cache.append({"vector": query_vec, "response": response, "timestamp": timestamp})
        if len(self.cache) > self.max_cache_size:
            self.cache.pop(0)

    def get_from_cache(self, query_vec):
        if not self.cache:
            return None
        cache_vectors = np.array([item["vector"] for item in self.cache])
        similarities = cosine_similarity([query_vec], cache_vectors)[0]
        best_match_idx = np.argmax(similarities)
        if similarities[best_match_idx] >= self.threshold:
            return self.cache[best_match_idx]["response"]
        return None
