class QueryCache:
    def __init__(self):
        self.cache = {}

    def get_cached_response(self, query):
        return self.cache.get(query)

    def cache_response(self, query, response):
        self.cache[query] = response