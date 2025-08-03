import cachetools, rapidfuzz, threading
class FixedMemory:
    def __init__(self, max_size=1024, ttl=3600):
        self.cache = cachetools.TTLCache(maxsize=max_size, ttl=ttl)
        self._lk = threading.RLock()
    def __setitem__(self, k, v):
        with self._lk: self.cache[k] = v
    def __getitem__(self, k):
        with self._lk: return self.cache.get(k)
    set = __setitem__; get = __getitem__
    def get_similar(self, q, thr=90):
        with self._lk:
            for k, v in self.cache.items():
                if rapidfuzz.fuzz.ratio(k, q) >= thr:
                    return v
        return None
