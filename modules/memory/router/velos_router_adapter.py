# VELOS 운영 철학 선언문: 파일명은 절대 변경하지 않는다. 수정 시 자가 검증을 포함하고,
# 실행 결과를 기록하며, 경로/구조는 불변으로 유지한다. 실패는 로깅하고 자동 복구를 시도한다.

import os
import sys
import time
from typing import Dict, List, Any, Optional

# VELOS 모듈 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'storage'))
from velos_adapter import VelosEnhancedMemoryAdapter

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'cache'))
from velos_cache_adapter import VelosCachedMemoryAdapter

# 쿼리 라우터 모듈
sys.path.append(os.path.dirname(__file__))
from query_router import search_memory, search_memory_advanced, get_cache_stats, clear_query_cache

# SQLite 저장소 모듈
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'storage'))
from sqlite_store import connect_db

# 역할별 검색 유틸리티
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'core', 'memory_adapter'))
from search import search_by_role_dict, search_roles_unified, search_with_normalized_query

# 명시적으로 utils 레벨 memory_adapter에서 import
from utils.memory_adapter import normalize_query


class VelosRouterMemoryAdapter(VelosCachedMemoryAdapter):
    """VELOS 메모리 어댑터 + 캐시 + 스마트 라우팅 통합"""

    def __init__(self, jsonl_path: Optional[str] = None, db_path: Optional[str] = None):
        super().__init__(jsonl_path, db_path)
        self.router_stats = {
            "keyword_searches": 0,
            "deep_searches": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }

    def smart_search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """스마트 검색 - 쿼리 타입에 따른 자동 라우팅"""
        start_time = time.time()

        # 항상 쿼리 정규화 적용
        q = normalize_query(query)

        # from: 패턴이 있으면 정규화된 검색 사용
        if "from:" in query:
            try:
                con = connect_db()
                cur = con.cursor()
                results = search_with_normalized_query(cur, query, limit)
                con.close()

                # 통계 업데이트
                search_time = time.time() - start_time
                self.router_stats["keyword_searches"] += 1

                return results
            except Exception as e:
                print(f"정규화된 검색 실패: {e}")
                # 폴백: 기존 방식 사용

        # 기존 쿼리 라우터 사용
        results = search_memory(q)

        # 통계 업데이트
        search_time = time.time() - start_time
        if len(query.strip()) <= 24 and " " not in query.strip():
            self.router_stats["keyword_searches"] += 1
        else:
            self.router_stats["deep_searches"] += 1

        # 결과 제한
        if len(results) > limit:
            results = results[:limit]

        return results

    def advanced_search(self, query: str,
                       days: Optional[int] = None,
                       limit: Optional[int] = None,
                       use_cache: bool = True) -> List[Dict[str, Any]]:
        """고급 검색 - 추가 옵션 지원"""
        return search_memory_advanced(query, days, limit, use_cache)

    def search_by_role(self, role: str, limit: int = 20) -> List[Dict[str, Any]]:
        """역할별 검색"""
        try:
            # 새로운 검색 유틸리티 사용
            con = connect_db()
            cur = con.cursor()

            results = search_by_role_dict(cur, role, limit)

            con.close()
            return results

        except Exception as e:
            print(f"역할별 검색 오류: {e}")
            # 폴백: 기존 방식 사용
            return self.smart_search(f"from:{role}", limit)

    def search_by_tag(self, tag: str, limit: int = 20) -> List[Dict[str, Any]]:
        """태그별 검색"""
        return self.smart_search(f"tag:{tag}", limit)

    def search_roles_unified(self, roles: List[str], limit_per_role: int = 10) -> Dict[str, List[Dict[str, Any]]]:
        """여러 역할을 한 번에 검색 - 통합된 쿼리"""
        try:
            con = connect_db()
            cur = con.cursor()

            results = search_roles_unified(cur, roles, limit_per_role)

            con.close()
            return results

        except Exception as e:
            print(f"통합 역할 검색 오류: {e}")
            # 폴백: 개별 검색
            result = {}
            for role in roles:
                result[role] = self.search_by_role(role, limit_per_role)
            return result

    def search_recent_by_days(self, days: int, limit: int = 20) -> List[Dict[str, Any]]:
        """최근 N일 검색"""
        since = int(time.time() - days * 86400)
        return self.advanced_search("", days=days, limit=limit)

    def get_router_stats(self) -> Dict[str, Any]:
        """라우터 통계 반환"""
        router_cache_stats = get_cache_stats()

        return {
            "router": self.router_stats,
            "router_cache": router_cache_stats,
            "adapter_cache": self.get_cache_stats()
        }

    def clear_all_caches(self) -> None:
        """모든 캐시 삭제"""
        super().invalidate_all_caches()
        clear_query_cache()

    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """종합 통계 반환"""
        base_stats = self.get_stats_enhanced()
        router_stats = self.get_router_stats()

        return {
            "memory": base_stats,
            "router": router_stats,
            "total_records": base_stats.get("db_records", 0),
            "total_cache_hits": (
                router_stats["router_cache"].get("hits", 0) +
                router_stats["adapter_cache"].get("search", {}).get("hits", 0)
            )
        }


def test_router_adapter():
    """라우터 어댑터 자가 검증 테스트"""
    print("=== VELOS Router Memory Adapter 테스트 ===")

    adapter = VelosRouterMemoryAdapter()

    print("1. 스마트 검색 테스트...")
    # 키워드 검색
    keyword_results = adapter.smart_search("VELOS", limit=5)
    print(f"   키워드 검색 결과: {len(keyword_results)}개")

    # 긴 쿼리 검색
    long_results = adapter.smart_search("VELOS 운영 철학", limit=5)
    print(f"   긴 쿼리 검색 결과: {len(long_results)}개")

    print("2. 고급 검색 테스트...")
    advanced_results = adapter.advanced_search("검색", days=7, limit=10)
    print(f"   고급 검색 결과: {len(advanced_results)}개")

    print("3. 역할별 검색 테스트...")
    role_results = adapter.search_by_role("user", limit=5)
    print(f"   사용자 역할 검색 결과: {len(role_results)}개")

    print("4. 최근 검색 테스트...")
    recent_results = adapter.search_recent_by_days(1, limit=5)
    print(f"   최근 1일 검색 결과: {len(recent_results)}개")

    print("5. 통계 테스트...")
    stats = adapter.get_router_stats()
    print(f"   라우터 통계: {stats}")

    print("6. 종합 통계 테스트...")
    comprehensive_stats = adapter.get_comprehensive_stats()
    print(f"   종합 통계: {comprehensive_stats}")

    print("=== Router Adapter 테스트 완료 ===")


if __name__ == "__main__":
    test_router_adapter()
    print("=== 모든 자가 검증 완료 ===")
