# [EXPERIMENT] VELOS 메모리 캐시 - 성능 최적화 모듈
# VELOS 운영 철학 선언문: 파일명은 절대 변경하지 않는다. 수정 시 자가 검증을 포함하고,
# 실행 결과를 기록하며, 경로/구조는 불변으로 유지한다. 실패는 로깅하고 자동 복구를 시도한다.
from __future__ import annotations

import time
from collections import OrderedDict
from typing import Any, Dict, Optional, Tuple


class TTLCache:
    """TTL 기반 메모리 캐시 - VELOS 시스템용"""

    def __init__(self, maxsize: int = 512, ttl: int = 600):
        self.maxsize = maxsize
        self.ttl = ttl
        self.store: "OrderedDict[str, Tuple[float, Any]]" = OrderedDict()
        self.stats = {"hits": 0, "misses": 0, "sets": 0, "evictions": 0}

    def get(self, key: str) -> Optional[Any]:
        """캐시에서 값 조회"""
        now = time.monotonic()
        if key in self.store:
            ts, val = self.store.pop(key)
            if now - ts < self.ttl:
                self.store[key] = (ts, val)
                self.stats["hits"] += 1
                return val
            else:
                # 만료된 항목 제거
                self.stats["misses"] += 1
        else:
            self.stats["misses"] += 1
        return None

    def set(self, key: str, value: Any) -> None:
        """캐시에 값 저장"""
        now = time.monotonic()
        if key in self.store:
            self.store.pop(key)
        elif len(self.store) >= self.maxsize:
            # LRU 제거
            self.store.popitem(last=False)
            self.stats["evictions"] += 1
        self.store[key] = (now, value)
        self.stats["sets"] += 1

    def clear(self) -> None:
        """캐시 전체 삭제"""
        self.store.clear()
        self.stats = {"hits": 0, "misses": 0, "sets": 0, "evictions": 0}

    def cleanup(self) -> int:
        """만료된 항목 정리"""
        now = time.monotonic()
        expired_keys = [key for key, (ts, _) in self.store.items() if now - ts >= self.ttl]
        for key in expired_keys:
            self.store.pop(key)
        return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계 반환"""
        hit_rate = 0
        if self.stats["hits"] + self.stats["misses"] > 0:
            hit_rate = self.stats["hits"] / (self.stats["hits"] + self.stats["misses"])

        return {
            "size": len(self.store),
            "maxsize": self.maxsize,
            "ttl": self.ttl,
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "sets": self.stats["sets"],
            "evictions": self.stats["evictions"],
            "hit_rate": hit_rate,
        }

    def keys(self) -> list:
        """캐시된 키 목록 반환"""
        return list(self.store.keys())


class VelosMemoryCache:
    """VELOS 메모리 캐시 관리자"""

    def __init__(self):
        self.caches: Dict[str, TTLCache] = {}

    def get_cache(self, name: str, maxsize: int = 512, ttl: int = 600) -> TTLCache:
        """캐시 인스턴스 반환 (없으면 생성)"""
        if name not in self.caches:
            self.caches[name] = TTLCache(maxsize, ttl)
        return self.caches[name]

    def clear_cache(self, name: str) -> bool:
        """특정 캐시 삭제"""
        if name in self.caches:
            self.caches[name].clear()
            return True
        return False

    def clear_all(self) -> None:
        """모든 캐시 삭제"""
        for cache in self.caches.values():
            cache.clear()

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """모든 캐시 통계 반환"""
        return {name: cache.get_stats() for name, cache in self.caches.items()}

    def cleanup_all(self) -> Dict[str, int]:
        """모든 캐시에서 만료된 항목 정리"""
        results = {}
        for name, cache in self.caches.items():
            results[name] = cache.cleanup()
        return results


def test_ttl_cache():
    """TTL 캐시 자가 검증 테스트"""
    print("=== VELOS TTL Cache 자가 검증 테스트 ===")

    # 기본 기능 테스트
    cache = TTLCache(maxsize=3, ttl=2)

    print("1. 기본 저장/조회 테스트...")
    cache.set("key1", "value1")
    cache.set("key2", "value2")

    assert cache.get("key1") == "value1"
    assert cache.get("key2") == "value2"
    assert cache.get("key3") is None
    print("   ✅ 기본 기능 정상")

    print("2. LRU 제거 테스트...")
    cache.set("key3", "value3")
    cache.set("key4", "value4")  # key1이 제거되어야 함

    assert cache.get("key1") is None
    assert cache.get("key4") == "value4"
    print("   ✅ LRU 제거 정상")

    print("3. TTL 만료 테스트...")
    cache.set("expire_test", "will_expire")
    assert cache.get("expire_test") == "will_expire"

    print("   3초 대기 중...")
    time.sleep(3)
    assert cache.get("expire_test") is None
    print("   ✅ TTL 만료 정상")

    print("4. 통계 테스트...")
    stats = cache.get_stats()
    assert "hits" in stats
    assert "misses" in stats
    assert "hit_rate" in stats
    print(f"   ✅ 통계: {stats}")

    print("=== TTL Cache 테스트 완료 ===")


def test_velos_cache_manager():
    """VELOS 캐시 관리자 자가 검증 테스트"""
    print("=== VELOS Cache Manager 자가 검증 테스트 ===")

    manager = VelosMemoryCache()

    print("1. 캐시 생성 테스트...")
    cache1 = manager.get_cache("test1", maxsize=10, ttl=5)
    cache2 = manager.get_cache("test2", maxsize=20, ttl=10)

    cache1.set("key1", "value1")
    cache2.set("key2", "value2")

    assert cache1.get("key1") == "value1"
    assert cache2.get("key2") == "value2"
    print("   ✅ 캐시 생성 정상")

    print("2. 통계 수집 테스트...")
    all_stats = manager.get_all_stats()
    assert "test1" in all_stats
    assert "test2" in all_stats
    print(f"   ✅ 통계: {all_stats}")

    print("3. 캐시 삭제 테스트...")
    assert manager.clear_cache("test1") is True
    assert manager.clear_cache("nonexistent") is False
    print("   ✅ 캐시 삭제 정상")

    print("=== Cache Manager 테스트 완료 ===")


if __name__ == "__main__":
    # 자가 검증 실행
    test_ttl_cache()
    print()
    test_velos_cache_manager()
    print("=== 모든 자가 검증 완료 ===")
