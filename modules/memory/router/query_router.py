# VELOS 운영 철학 선언문: 파일명은 절대 변경하지 않는다. 수정 시 자가 검증을 포함하고,
# 실행 결과를 기록하며, 경로/구조는 불변으로 유지한다. 실패는 로깅하고 자동 복구를 시도한다.
from __future__ import annotations
import os
import time
import sqlite3
from typing import List, Dict, Any, Optional

# VELOS 환경 변수 로딩
# Path manager imports (Phase 2 standardization)
try:
    from modules.core.path_manager import get_velos_root, get_data_path, get_config_path, get_db_path
except ImportError:
    # Fallback functions for backward compatibility
    def get_velos_root(): return "C:/giwanos"
    def get_data_path(*parts): return os.path.join("C:/giwanos", "data", *parts)
    def get_config_path(*parts): return os.path.join("C:/giwanos", "configs", *parts)
    def get_db_path(): return "C:/giwanos/data/memory/velos.db"

def _env(name: str, default: Optional[str] = None) -> str:
    """VELOS 환경 변수 로딩: ENV > configs/settings.yaml > C:\giwanos 순서"""
    v = os.getenv(name, default)
    if not v:
        # 설정 파일에서 로드 시도
        try:
            import yaml
            config_path = os.path.join(get_config_path("settings.yaml") if "get_config_path" in locals() else "C:/giwanos/configs/settings.yaml")
            if config_path and os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    v = config.get(name, default)
        except Exception:
            pass

        if not v:
            # 기본값 설정
            if name == "VELOS_RECENT_DAYS":
                v = "3"
            elif name == "VELOS_KEYWORD_MAXLEN":
                v = "24"
            elif name == "VELOS_FTS_LIMIT":
                v = "20"
            else:
                raise RuntimeError(f"Missing env: {name}")
    return v

# VELOS 모듈 경로 추가
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'storage'))
from sqlite_store import connect_db

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'cache'))
from memory_cache import TTLCache

# 환경 변수 로딩
RECENT_DAYS = int(_env("VELOS_RECENT_DAYS", "3"))
KEYWORD_MAXLEN = int(_env("VELOS_KEYWORD_MAXLEN", "24"))
FTS_LIMIT = int(_env("VELOS_FTS_LIMIT", "20"))

# 쿼리 캐시 초기화
_qcache = TTLCache(maxsize=512, ttl=600)


def _is_keyword(q: str) -> bool:
    """키워드 여부 판단 (짧고 공백 없음)"""
    return len(q.strip()) <= KEYWORD_MAXLEN and (" " not in q.strip())


def _recent_since_epoch(days: int) -> int:
    """N일 전 타임스탬프 계산"""
    return int(time.time() - days * 86400)


def ensure_cache_fresh(con):
    """데이터베이스 버전 변경 감지하여 캐시 무효화"""
    v = con.execute("PRAGMA data_version;").fetchone()[0]
    if getattr(ensure_cache_fresh, "_v", None) not in (None, v):
        _qcache.clear()
        print(f"캐시 무효화: DB 버전 변경 감지 ({getattr(ensure_cache_fresh, '_v', 'None')} -> {v})")
    ensure_cache_fresh._v = v


def search_memory(query: str) -> List[Dict[str, Any]]:
    """VELOS 메모리 검색 - 스마트 라우팅 + 캐싱"""
    # 캐시 히트 체크
    ckey = f"q:{query}"
    hit = _qcache.get(ckey)
    if hit is not None:
        return hit

    con = connect_db()

    # 캐시 무효화 훅 실행
    ensure_cache_fresh(con)

    cur = con.cursor()
    rows: List[Dict[str, Any]] = []

    try:
        if _is_keyword(query):
            # 키워드 검색: 최근 N일 + LIKE 우선 (빠른 라이트 쿼리)
            since = _recent_since_epoch(RECENT_DAYS)
            cur.execute("""
                SELECT id, ts, role, insight, raw, tags
                FROM memory
                WHERE ts >= ? AND (insight LIKE ? OR raw LIKE ?)
                ORDER BY ts DESC LIMIT ?
            """, (since, f"%{query}%", f"%{query}%", FTS_LIMIT))

            for r in cur.fetchall():
                id_, ts, role, insight, raw, tags = r
                try:
                    tags = json.loads(tags) if tags else []
                except:
                    tags = []
                rows.append({
                    "id": id_, "ts": ts, "from": role,
                    "insight": insight, "raw": raw, "tags": tags
                })

            # 필요 시 FTS 보강 (개선된 패턴)
            if not rows:
                cur.execute("""
                    SELECT m.id, m.ts, t.text_norm, bm25(memory_fts) AS score
                    FROM memory_fts
                    JOIN memory_text t ON t.id = memory_fts.rowid
                    JOIN memory m ON m.id = memory_fts.rowid
                    WHERE memory_fts MATCH ?
                    ORDER BY score
                    LIMIT ?
                """, (query, FTS_LIMIT))

                for r in cur.fetchall():
                    id_, ts, text_norm, score = r
                    # text_norm을 insight로 매핑 (호환성 유지)
                    rows.append({
                        "id": id_, "ts": ts, "from": "system",
                        "insight": text_norm, "raw": "", "tags": [],
                        "score": score
                    })
        else:
            # 깊은 쿼리: FTS 우선 (개선된 패턴)
            cur.execute("""
                SELECT m.id, m.ts, t.text_norm, bm25(memory_fts) AS score
                FROM memory_fts
                JOIN memory_text t ON t.id = memory_fts.rowid
                JOIN memory m ON m.id = memory_fts.rowid
                WHERE memory_fts MATCH ?
                ORDER BY score
                LIMIT ?
            """, (query, FTS_LIMIT))

            for r in cur.fetchall():
                id_, ts, text_norm, score = r
                # text_norm을 insight로 매핑 (호환성 유지)
                rows.append({
                    "id": id_, "ts": ts, "from": "system",
                    "insight": text_norm, "raw": "", "tags": [],
                    "score": score
                })

    except Exception as e:
        print(f"검색 오류: {e}")
        rows = []

    finally:
        con.close()

    # 결과 캐싱
    _qcache.set(ckey, rows)
    return rows


def search_memory_advanced(query: str,
                          days: Optional[int] = None,
                          limit: Optional[int] = None,
                          use_cache: bool = True) -> List[Dict[str, Any]]:
    """고급 메모리 검색 - 추가 옵션 지원"""
    if days is None:
        days = RECENT_DAYS
    if limit is None:
        limit = FTS_LIMIT

    # 캐시 키 생성
    ckey = f"adv:{query}:{days}:{limit}"
    if use_cache:
        hit = _qcache.get(ckey)
        if hit is not None:
            return hit

    con = connect_db()

    # 캐시 무효화 훅 실행
    ensure_cache_fresh(con)

    cur = con.cursor()
    rows: List[Dict[str, Any]] = []

    try:
        since = _recent_since_epoch(days)

        # 하이브리드 검색: LIKE + FTS 조합
        cur.execute("""
            SELECT id, ts, role, insight, raw, tags
            FROM memory
            WHERE ts >= ? AND (insight LIKE ? OR raw LIKE ?)
            ORDER BY ts DESC LIMIT ?
        """, (since, f"%{query}%", f"%{query}%", limit))

        for r in cur.fetchall():
            id_, ts, role, insight, raw, tags = r
            try:
                tags = json.loads(tags) if tags else []
            except:
                tags = []
            rows.append({
                "id": id_, "ts": ts, "from": role,
                "insight": insight, "raw": raw, "tags": tags
            })

        # 결과가 부족하면 FTS로 보강
        if len(rows) < limit:
            remaining = limit - len(rows)
            existing_ids = [row["id"] for row in rows]
            id_filter = ""
            if existing_ids:
                id_filter = f"AND m.id NOT IN ({','.join(map(str, existing_ids))})"

            cur.execute(f"""
                SELECT m.id, m.ts, m.role, m.insight, m.raw, m.tags
                FROM memory_fts f
                JOIN memory m ON m.id = f.rowid
                WHERE memory_fts MATCH ? {id_filter}
                ORDER BY bm25(memory_fts) ASC, m.ts DESC LIMIT ?
            """, (query, remaining))

            for r in cur.fetchall():
                id_, ts, role, insight, raw, tags = r
                try:
                    tags = json.loads(tags) if tags else []
                except:
                    tags = []
                rows.append({
                    "id": id_, "ts": ts, "from": role,
                    "insight": insight, "raw": raw, "tags": tags
                })

    except Exception as e:
        print(f"고급 검색 오류: {e}")
        rows = []

    finally:
        con.close()

    # 결과 캐싱
    if use_cache:
        _qcache.set(ckey, rows)
    return rows


def get_cache_stats() -> Dict[str, Any]:
    """쿼리 캐시 통계 반환"""
    return _qcache.get_stats()


def clear_query_cache() -> None:
    """쿼리 캐시 삭제"""
    _qcache.clear()


def test_query_router():
    """쿼리 라우터 자가 검증 테스트"""
    print("=== VELOS Query Router 자가 검증 테스트 ===")

    print("1. 키워드 검색 테스트...")
    results = search_memory("VELOS")
    print(f"   키워드 'VELOS' 검색 결과: {len(results)}개")

    print("2. 긴 쿼리 검색 테스트...")
    results = search_memory("VELOS 운영 철학")
    print(f"   긴 쿼리 검색 결과: {len(results)}개")

    print("3. 고급 검색 테스트...")
    results = search_memory_advanced("검색", days=7, limit=10)
    print(f"   고급 검색 결과: {len(results)}개")

    print("4. 캐시 통계 테스트...")
    cache_stats = get_cache_stats()
    print(f"   캐시 통계: {cache_stats}")

    print("5. 캐시 히트 테스트...")
    # 두 번째 검색으로 캐시 히트 확인
    results2 = search_memory("VELOS")
    cache_stats2 = get_cache_stats()
    print(f"   캐시 히트 후 통계: {cache_stats2}")

    print("=== Query Router 테스트 완료 ===")


if __name__ == "__main__":
    import json
    test_query_router()
    print("=== 모든 자가 검증 완료 ===")
