#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VELOS 운영 철학 선언문: 파일명은 절대 변경하지 않는다. 수정 시 자가 검증을 포함하고,
실행 결과를 기록하며, 경로/구조는 불변으로 유지한다. 실패는 로깅하고 자동 복구를
시도한다.

표준화된 FTS 검색 유틸리티
새로운 검색 패턴을 일관되게 적용하기 위한 유틸리티 함수들입니다.
"""

import os
import sqlite3
from typing import List, Dict, Any, Optional, Tuple
import json

# 환경변수에서 DB 경로 가져오기
DB = os.getenv("VELOS_DB", r"C:\giwanos\data\velos.db")


def search_fts(term: str, limit: int = 20) -> List[Tuple]:
    """
    ✅ 표준 FTS 검색 함수

    Args:
        term: 검색어
        limit: 최대 결과 수

    Returns:
        검색 결과 리스트 (id, ts, text_norm, score)
    """
    con = sqlite3.connect(DB)
    cur = con.cursor()

    sql = """
    SELECT m.id, m.ts, t.text_norm, bm25(memory_fts) AS score
    FROM memory_fts
    JOIN memory_text t ON t.id = memory_fts.rowid
    JOIN memory m ON m.id = memory_fts.rowid
    WHERE memory_fts MATCH ?
    ORDER BY score
    LIMIT ?
    """
    rows = cur.execute(sql, (term, limit)).fetchall()
    con.close()
    return rows


def search_fts_with_metadata(term: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    ✅ FTS 검색 + 메타데이터 포함

    Args:
        term: 검색어
        limit: 최대 결과 수

    Returns:
        검색 결과 딕셔너리 리스트
    """
    con = sqlite3.connect(DB)
    cur = con.cursor()

    sql = """
    SELECT m.id, m.ts, m.role, t.text_norm, m.tags, bm25(memory_fts) AS score
    FROM memory_fts
    JOIN memory_text t ON t.id = memory_fts.rowid
    JOIN memory m ON m.id = memory_fts.rowid
    WHERE memory_fts MATCH ?
    ORDER BY score
    LIMIT ?
    """
    rows = cur.execute(sql, (term, limit)).fetchall()
    con.close()

    results = []
    for row in rows:
        id_, ts, role, text_norm, tags, score = row
        try:
            tags = json.loads(tags) if tags else []
        except:
            tags = []

        results.append({
            "id": id_,
            "ts": ts,
            "role": role,
            "text_norm": text_norm,
            "tags": tags,
            "score": score
        })

    return results


def search_fts_by_role(term: str, role: str, limit: int = 20) -> List[Tuple]:
    """
    ✅ 역할별 FTS 검색

    Args:
        term: 검색어
        role: 역할 ('user', 'system', 'test')
        limit: 최대 결과 수

    Returns:
        검색 결과 리스트
    """
    con = sqlite3.connect(DB)
    cur = con.cursor()

    sql = """
    SELECT m.id, m.ts, t.text_norm, bm25(memory_fts) AS score
    FROM memory_fts
    JOIN memory_text t ON t.id = memory_fts.rowid
    JOIN memory m ON m.id = memory_fts.rowid
    WHERE memory_fts MATCH ? AND m.role = ?
    ORDER BY score
    LIMIT ?
    """
    rows = cur.execute(sql, (term, role, limit)).fetchall()
    con.close()
    return rows


def search_fts_recent(term: str, hours: int = 24, limit: int = 20) -> List[Tuple]:
    """
    ✅ 최근 데이터 FTS 검색

    Args:
        term: 검색어
        hours: 최근 시간 (시간 단위)
        limit: 최대 결과 수

    Returns:
        검색 결과 리스트
    """
    import time
    since_ts = int(time.time()) - (hours * 3600)

    con = sqlite3.connect(DB)
    cur = con.cursor()

    sql = """
    SELECT m.id, m.ts, t.text_norm, bm25(memory_fts) AS score
    FROM memory_fts
    JOIN memory_text t ON t.id = memory_fts.rowid
    JOIN memory m ON m.id = memory_fts.rowid
    WHERE memory_fts MATCH ? AND m.ts >= ?
    ORDER BY score
    LIMIT ?
    """
    rows = cur.execute(sql, (term, since_ts, limit)).fetchall()
    con.close()
    return rows


def get_search_stats(term: str) -> Dict[str, Any]:
    """
    ✅ 검색 통계 조회

    Args:
        term: 검색어

    Returns:
        검색 통계 정보
    """
    con = sqlite3.connect(DB)
    cur = con.cursor()

    # 전체 결과 수
    total_count = cur.execute("""
        SELECT COUNT(*) FROM memory_fts WHERE memory_fts MATCH ?
    """, (term,)).fetchone()[0]

    # 역할별 통계
    role_stats = {}
    for role in ['user', 'system', 'test']:
        count = cur.execute("""
            SELECT COUNT(*) FROM memory_fts f
            JOIN memory m ON m.id = f.rowid
            WHERE memory_fts MATCH ? AND m.role = ?
        """, (term, role)).fetchone()[0]
        role_stats[role] = count

    # 점수 통계
    scores = cur.execute("""
        SELECT bm25(memory_fts) FROM memory_fts
        WHERE memory_fts MATCH ?
        ORDER BY bm25(memory_fts)
        LIMIT 10
    """, (term,)).fetchall()

    score_stats = {}
    if scores:
        score_values = [s[0] for s in scores]
        score_stats = {
            "min": min(score_values),
            "max": max(score_values),
            "avg": sum(score_values) / len(score_values)
        }

    con.close()

    return {
        "term": term,
        "total_count": total_count,
        "role_stats": role_stats,
        "score_stats": score_stats
    }


def search_fts_batch(terms: List[str], limit: int = 10) -> Dict[str, List[Tuple]]:
    """
    ✅ 배치 FTS 검색

    Args:
        terms: 검색어 리스트
        limit: 각 검색어당 최대 결과 수

    Returns:
        검색어별 결과 딕셔너리
    """
    results = {}
    for term in terms:
        results[term] = search_fts(term, limit)
    return results


# 호환성을 위한 별칭 함수들
def search(term: str, limit: int = 20) -> List[Tuple]:
    """search_fts의 별칭"""
    return search_fts(term, limit)


def search_with_metadata(term: str, limit: int = 20) -> List[Dict[str, Any]]:
    """search_fts_with_metadata의 별칭"""
    return search_fts_with_metadata(term, limit)


if __name__ == "__main__":
    # 자체 테스트
    print("VELOS FTS 검색 유틸리티 테스트")
    print("=" * 40)

    # 기본 검색 테스트
    test_terms = ["VELOS", "테스트", "메모리"]

    for term in test_terms:
        print(f"\n-- '{term}' 검색 --")
        results = search_fts(term, 5)
        print(f"결과: {len(results)}개")

        if results:
            print("상위 결과:")
            for i, (id_, ts, text_norm, score) in enumerate(results[:3]):
                preview = text_norm[:50] + "..." if len(text_norm) > 50 else text_norm
                print(f"  {i+1}. ID {id_} (점수: {score:.2f}): {preview}")

    # 통계 테스트
    print(f"\n-- 검색 통계 --")
    stats = get_search_stats("VELOS")
    print(f"총 결과: {stats['total_count']}개")
    print(f"역할별: {stats['role_stats']}")
    if stats['score_stats']:
        print(f"점수: {stats['score_stats']}")

    print("\n✅ FTS 검색 유틸리티 테스트 완료")
