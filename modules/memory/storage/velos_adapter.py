# VELOS 운영 철학 선언문: 파일명은 절대 변경하지 않는다. 수정 시 자가 검증을 포함하고,
# 실행 결과를 기록하며, 경로/구조는 불변으로 유지한다. 실패는 로깅하고 자동 복구를 시도한다.

import json
import os
import sys
import time
from typing import Any, Dict, List, Optional

# 기존 VELOS 모듈 경로 추가
from modules.core.memory_adapter import MemoryAdapter

# 새로운 저장소 모듈
sys.path.append(os.path.dirname(__file__))
from sqlite_store import VelosMemoryStore


class VelosEnhancedMemoryAdapter(MemoryAdapter):
    """VELOS 메모리 어댑터 확장 - FTS5 검색 및 크로스프로세스 락 지원"""

    def __init__(self, jsonl_path: Optional[str] = None, db_path: Optional[str] = None):
        super().__init__(jsonl_path, db_path)
        self._fts_store = None

    def _get_fts_store(self) -> VelosMemoryStore:
        """FTS 저장소 인스턴스 반환 (지연 초기화)"""
        if self._fts_store is None:
            self._fts_store = VelosMemoryStore(self.db)
        return self._fts_store

    def search_fts(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """FTS5 전체 텍스트 검색"""
        try:
            with self._get_fts_store() as store:
                return store.search_fts(query, limit)
        except Exception as e:
            print(f"FTS 검색 실패: {e}")
            # 폴백: 기존 검색 사용
            return self.search(query, limit)

    def get_recent_enhanced(self, limit: int = 20) -> List[Dict[str, Any]]:
        """향상된 최근 메모리 조회 (ID 포함)"""
        try:
            with self._get_fts_store() as store:
                return store.get_recent(limit)
        except Exception as e:
            print(f"향상된 조회 실패: {e}")
            # 폴백: 기존 조회 사용
            return self.recent(limit)

    def insert_direct(
        self, ts: int, role: str, insight: str, raw: str = "", tags: list = None
    ) -> int:
        """직접 DB 삽입 (JSONL 우회)"""
        try:
            with self._get_fts_store() as store:
                return store.insert_memory(ts, role, insight, raw, tags or [])
        except Exception as e:
            print(f"직접 삽입 실패: {e}")
            # 폴백: JSONL 사용
            item = {"ts": ts, "from": role, "insight": insight, "raw": raw, "tags": tags or []}
            self.append_jsonl(item)
            return -1  # ID 알 수 없음

    def get_stats_enhanced(self) -> Dict[str, Any]:
        """향상된 통계 (FTS 정보 포함)"""
        stats = self.get_stats()

        try:
            with self._get_fts_store() as store:
                # FTS 테이블 크기 확인
                cur = store.con.cursor()
                (fts_count,) = cur.execute("SELECT COUNT(*) FROM memory_fts").fetchone()
                stats["fts_records"] = fts_count

                # 락 테이블 상태 확인
                (lock_count,) = cur.execute("SELECT COUNT(*) FROM locks").fetchone()
                stats["active_locks"] = lock_count

        except Exception as e:
            stats["fts_records"] = 0
            stats["active_locks"] = 0
            stats["fts_error"] = str(e)

        return stats


def test_enhanced_adapter():
    """향상된 어댑터 테스트"""
    print("=== VELOS Enhanced Memory Adapter 테스트 ===")

    adapter = VelosEnhancedMemoryAdapter()

    # 기존 기능 테스트
    print("1. 기존 기능 테스트...")
    stats = adapter.get_stats()
    print(f"   기존 통계: {stats}")

    # 새로운 기능 테스트
    print("2. FTS 검색 테스트...")
    fts_results = adapter.search_fts("VELOS", limit=5)
    print(f"   FTS 검색 결과: {len(fts_results)}개")

    print("3. 향상된 통계 테스트...")
    enhanced_stats = adapter.get_stats_enhanced()
    print(f"   향상된 통계: {enhanced_stats}")

    print("4. 직접 삽입 테스트...")
    memory_id = adapter.insert_direct(
        ts=int(time.time()),
        role="test",
        insight="향상된 어댑터 테스트",
        raw="직접 DB 삽입 테스트",
        tags=["test", "enhanced"],
    )
    print(f"   삽입된 ID: {memory_id}")

    print("=== 테스트 완료 ===")


if __name__ == "__main__":
    test_enhanced_adapter()
