# VELOS 운영 철학 선언문: 파일명은 절대 변경하지 않는다. 수정 시 자가 검증을 포함하고,
# 실행 결과를 기록하며, 경로/구조는 불변으로 유지한다. 실패는 로깅하고 자동 복구를 시도한다.

import os
import sys
import time
from typing import Dict, List, Any, Optional

# VELOS 모듈 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'storage'))
from velos_adapter import VelosEnhancedMemoryAdapter

# 캐시 모듈
sys.path.append(os.path.dirname(__file__))
from memory_cache import VelosMemoryCache


class VelosCachedMemoryAdapter(VelosEnhancedMemoryAdapter):
    """VELOS 메모리 어댑터 + 캐시 통합"""

    def __init__(self, jsonl_path: Optional[str] = None, db_path: Optional[str] = None):
        super().__init__(jsonl_path, db_path)
        self.cache_manager = VelosMemoryCache()

        # 기본 캐시들 초기화
        self.search_cache = self.cache_manager.get_cache("search", maxsize=256, ttl=300)
        self.recent_cache = self.cache_manager.get_cache("recent", maxsize=128, ttl=60)
        self.stats_cache = self.cache_manager.get_cache("stats", maxsize=64, ttl=120)

    def search_fts_cached(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """FTS 검색 + 캐시"""
        cache_key = f"search:{query}:{limit}"
        cached = self.search_cache.get(cache_key)
        if cached is not None:
            return cached

        # 캐시 미스: 실제 검색 실행
        results = self.search_fts(query, limit)
        self.search_cache.set(cache_key, results)
        return results

    def get_recent_cached(self, limit: int = 20) -> List[Dict[str, Any]]:
        """최근 메모리 조회 + 캐시"""
        cache_key = f"recent:{limit}"
        cached = self.recent_cache.get(cache_key)
        if cached is not None:
            return cached

        # 캐시 미스: 실제 조회 실행
        results = self.get_recent_enhanced(limit)
        self.recent_cache.set(cache_key, results)
        return results

    def get_stats_cached(self) -> Dict[str, Any]:
        """통계 조회 + 캐시"""
        cache_key = "stats"
        cached = self.stats_cache.get(cache_key)
        if cached is not None:
            return cached

        # 캐시 미스: 실제 통계 계산
        stats = self.get_stats_enhanced()
        self.stats_cache.set(cache_key, stats)
        return stats

    def invalidate_search_cache(self) -> None:
        """검색 캐시 무효화"""
        self.search_cache.clear()

    def invalidate_recent_cache(self) -> None:
        """최근 조회 캐시 무효화"""
        self.recent_cache.clear()

    def invalidate_stats_cache(self) -> None:
        """통계 캐시 무효화"""
        self.stats_cache.clear()

    def invalidate_all_caches(self) -> None:
        """모든 캐시 무효화"""
        self.cache_manager.clear_all()

    def get_cache_stats(self) -> Dict[str, Dict[str, Any]]:
        """캐시 통계 반환"""
        return self.cache_manager.get_all_stats()

    def cleanup_expired_cache(self) -> Dict[str, int]:
        """만료된 캐시 항목 정리"""
        return self.cache_manager.cleanup_all()

    def append_jsonl(self, item: Dict[str, Any]) -> None:
        """JSONL 추가 + 캐시 무효화"""
        super().append_jsonl(item)
        # 데이터 변경 시 관련 캐시 무효화
        self.invalidate_recent_cache()
        self.invalidate_stats_cache()

    def insert_direct(self, ts: int, role: str, insight: str,
                     raw: str = "", tags: list = None) -> int:
        """직접 삽입 + 캐시 무효화"""
        result = super().insert_direct(ts, role, insight, raw, tags)
        # 데이터 변경 시 관련 캐시 무효화
        self.invalidate_recent_cache()
        self.invalidate_stats_cache()
        return result


def test_cached_adapter():
    """캐시 어댑터 자가 검증 테스트"""
    print("=== VELOS Cached Memory Adapter 테스트 ===")

    adapter = VelosCachedMemoryAdapter()

    print("1. 캐시된 검색 테스트...")
    # 첫 번째 검색 (캐시 미스)
    start_time = time.time()
    results1 = adapter.search_fts_cached("VELOS", limit=5)
    time1 = time.time() - start_time

    # 두 번째 검색 (캐시 히트)
    start_time = time.time()
    results2 = adapter.search_fts_cached("VELOS", limit=5)
    time2 = time.time() - start_time

    print(f"   첫 번째 검색: {time1:.4f}초")
    print(f"   두 번째 검색: {time2:.4f}초")
    if time2 > 0:
        print(f"   캐시 효과: {time1/time2:.1f}배 빨라짐")
    else:
        print("   캐시 효과: 매우 빠름 (측정 불가)")

    print("2. 캐시된 최근 조회 테스트...")
    recent1 = adapter.get_recent_cached(limit=10)
    recent2 = adapter.get_recent_cached(limit=10)
    assert len(recent1) == len(recent2)
    print(f"   최근 레코드: {len(recent1)}개")

    print("3. 캐시 통계 테스트...")
    cache_stats = adapter.get_cache_stats()
    print(f"   캐시 통계: {cache_stats}")

    print("4. 캐시 무효화 테스트...")
    adapter.invalidate_search_cache()
    adapter.invalidate_recent_cache()
    print("   ✅ 캐시 무효화 완료")

    print("5. 만료된 캐시 정리 테스트...")
    cleaned = adapter.cleanup_expired_cache()
    print(f"   정리된 항목: {cleaned}")

    print("=== 캐시 어댑터 테스트 완료 ===")


if __name__ == "__main__":
    test_cached_adapter()
    print("=== 모든 자가 검증 완료 ===")
