import cachetools
import rapidfuzz
import threading
from modules.core.error_handler import handle_exception

class FixedMemory:
    def __init__(self, max_size=1024, ttl=3600):
        self.cache = cachetools.TTLCache(maxsize=max_size, ttl=ttl)
        self._lk = threading.RLock()

    def __setitem__(self, k, v):
        try:
            with self._lk:
                self.cache[k] = v
        except Exception as e:
            handle_exception(e, context="FixedMemory 저장 실패")

    def __getitem__(self, k):
        try:
            with self._lk:
                return self.cache.get(k)
        except Exception as e:
            handle_exception(e, context="FixedMemory 조회 실패")
            return None

    def get_similar(self, q, thr=90):
        try:
            with self._lk:
                for k, v in self.cache.items():
                    if rapidfuzz.fuzz.ratio(k, q) >= thr:
                        return v
            return None
        except Exception as e:
            handle_exception(e, context="FixedMemory 유사 데이터 조회 실패")
            return None


