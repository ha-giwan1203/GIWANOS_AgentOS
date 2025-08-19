# [ACTIVE] VELOS 운영 철학 선언문: 파일명은 절대 변경하지 않는다. 수정 시 자가 검증을 포함하고,
# 실행 결과를 기록하며, 경로/구조는 불변으로 유지한다. 실패는 로깅하고 자동 복구를 시도한다.

"""
VELOS 메모리 역할별 검색 유틸리티

기존의 'from:' 패턴 문제를 해결하고 역할별 검색을 위한 표준화된 함수들을 제공합니다.
"""

import sqlite3
import re
from typing import List, Dict, Any, Optional, Tuple


def normalize_query(q: str) -> str:
    """
    쿼리 정규화 - from: 패턴을 role: 패턴으로 변환

    Args:
        q: 원본 쿼리 문자열

    Returns:
        str: 정규화된 쿼리 문자열

    Examples:
        "from:system VELOS" -> "role:system VELOS"
        "from:user test" -> "role:user test"
    """
    return (q
            .replace("from:user", "role:user")
            .replace("from:system", "role:system")
            .replace("from:test", "role:test"))


def search_by_role(cur: sqlite3.Cursor, role: str, limit: int = 10) -> List[Tuple[Any, ...]]:
    """
    역할별 검색 - memory_roles 뷰 사용

    Args:
        cur: SQLite 커서
        role: 'user' | 'system' | 'test' 등
        limit: 반환할 최대 레코드 수

    Returns:
        List[Tuple]: 검색 결과 튜플 리스트
    """
    sql = """
    SELECT id, ts, role, source, text
    FROM memory_roles
    WHERE role = ?
    ORDER BY ts DESC
    LIMIT ?
    """
    return cur.execute(sql, (role, limit)).fetchall()


def search_by_role_dict(cur: sqlite3.Cursor, role: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    역할별 검색 - 딕셔너리 형태로 반환

    Args:
        cur: SQLite 커서
        role: 'user' | 'system' | 'test' 등
        limit: 반환할 최대 레코드 수

    Returns:
        List[Dict]: 검색 결과 딕셔너리 리스트
    """
    rows = search_by_role(cur, role, limit)
    results = []

    for row in rows:
        id_val, ts, role_val, source, text = row
        results.append({
            "id": id_val,
            "ts": ts,
            "role": role_val,
            "source": source,
            "text": text,
            "from": role_val  # 호환성을 위한 별칭
        })

    return results


def search_roles_unified(cur: sqlite3.Cursor, roles: List[str], limit_per_role: int = 10) -> Dict[str, List[Dict[str, Any]]]:
    """
    여러 역할을 한 번에 검색 - 통합된 쿼리

    Args:
        cur: SQLite 커서
        roles: 검색할 역할 리스트 ['user', 'system', 'test']
        limit_per_role: 역할당 최대 레코드 수

    Returns:
        Dict[str, List[Dict]]: 역할별 검색 결과
    """
    result = {}

    for role in roles:
        result[role] = search_by_role_dict(cur, role, limit_per_role)

    return result


def search_by_role_advanced(cur: sqlite3.Cursor, role: str, days: Optional[int] = None,
                          limit: int = 10) -> List[Dict[str, Any]]:
    """
    고급 역할별 검색 - 시간 필터링 지원

    Args:
        cur: SQLite 커서
        role: 'user' | 'system' | 'test' 등
        days: 최근 N일 (None이면 전체)
        limit: 반환할 최대 레코드 수

    Returns:
        List[Dict]: 검색 결과 딕셔너리 리스트
    """
    if days is not None:
        import time
        since = int(time.time() - days * 86400)
        sql = """
        SELECT id, ts, role, source, text
        FROM memory_roles
        WHERE role = ? AND ts >= ?
        ORDER BY ts DESC
        LIMIT ?
        """
        rows = cur.execute(sql, (role, since, limit)).fetchall()
    else:
        rows = search_by_role(cur, role, limit)

    results = []
    for row in rows:
        id_val, ts, role_val, source, text = row
        results.append({
            "id": id_val,
            "ts": ts,
            "role": role_val,
            "source": source,
            "text": text,
            "from": role_val
        })

    return results


def get_role_statistics(cur: sqlite3.Cursor) -> Dict[str, int]:
    """
    역할별 통계 조회

    Args:
        cur: SQLite 커서

    Returns:
        Dict[str, int]: 역할별 레코드 수
    """
    sql = """
    SELECT role, COUNT(*) as count
    FROM memory_roles
    GROUP BY role
    ORDER BY count DESC
    """

    rows = cur.execute(sql).fetchall()
    stats = {}

    for role, count in rows:
        stats[role] = count

    return stats


def search_by_role_with_keyword(cur: sqlite3.Cursor, role: str, keyword: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    역할별 + 키워드 검색

    Args:
        cur: SQLite 커서
        role: 'user' | 'system' | 'test' 등
        keyword: 검색할 키워드
        limit: 반환할 최대 레코드 수

    Returns:
        List[Dict]: 검색 결과 딕셔너리 리스트
    """
    sql = """
    SELECT id, ts, role, source, text
    FROM memory_roles
    WHERE insight LIKE ?
    ORDER BY ts DESC
    LIMIT ?
    """

    keyword_pattern = f"%{keyword}%"
    rows = cur.execute(sql, (role, keyword_pattern, limit)).fetchall()

    results = []
    for row in rows:
        id_val, ts, role_val, source, text = row
        results.append({
            "id": id_val,
            "ts": ts,
            "role": role_val,
            "source": source,
            "text": text,
            "from": role_val
        })

    return results


def search_with_normalized_query(cur: sqlite3.Cursor, query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    정규화된 쿼리로 검색 - from: 패턴을 자동으로 role: 패턴으로 변환

    Args:
        cur: SQLite 커서
        query: 검색 쿼리 (from: 패턴 포함 가능)
        limit: 반환할 최대 레코드 수

    Returns:
        List[Dict]: 검색 결과 딕셔너리 리스트
    """
    # 쿼리 정규화
    normalized_query = normalize_query(query)

    # role: 패턴이 있는지 확인
    role_match = re.search(r'role:(\w+)', normalized_query)

    if role_match:
        # 역할별 검색
        role = role_match.group(1)
        # 나머지 키워드 추출
        remaining_query = normalized_query.replace(f'role:{role}', '').strip()

        if remaining_query:
            # 역할 + 키워드 검색
            return search_by_role_with_keyword(cur, role, remaining_query, limit)
        else:
            # 역할만 검색
            return search_by_role_dict(cur, role, limit)
    else:
        # 일반 키워드 검색
        sql = """
        SELECT id, ts, role, source, text
        FROM memory_roles
        WHERE insight LIKE ?
        ORDER BY ts DESC
        LIMIT ?
        """

        keyword_pattern = f"%{normalized_query}%"
        rows = cur.execute(sql, (keyword_pattern, limit)).fetchall()

        results = []
        for row in rows:
            id_val, ts, role_val, source, text = row
            results.append({
                "id": id_val,
                "ts": ts,
                "role": role_val,
                "source": source,
                "text": text,
                "from": role_val
            })

        return results


# 호환성을 위한 별칭 함수들
def get_user_messages(cur: sqlite3.Cursor, limit: int = 10) -> List[Dict[str, Any]]:
    """사용자 메시지 조회 (호환성)"""
    return search_by_role_dict(cur, 'user', limit)


def get_system_messages(cur: sqlite3.Cursor, limit: int = 10) -> List[Dict[str, Any]]:
    """시스템 메시지 조회 (호환성)"""
    return search_by_role_dict(cur, 'system', limit)


def get_test_messages(cur: sqlite3.Cursor, limit: int = 10) -> List[Dict[str, Any]]:
    """테스트 메시지 조회 (호환성)"""
    return search_by_role_dict(cur, 'test', limit)


if __name__ == "__main__":
    """자가 검증 테스트"""
    import os

    # VELOS DB 경로 설정
    db_path = os.getenv('VELOS_DB', 'C:/giwanos/data/velos.db')

    if not os.path.exists(db_path):
        print(f"❌ 데이터베이스 파일이 존재하지 않습니다: {db_path}")
        exit(1)

    try:
        conn = sqlite3.connect(db_path, timeout=5)
        cur = conn.cursor()

        print("=== VELOS 역할별 검색 유틸리티 자가 검증 ===")

        # 1. 역할별 통계 확인
        stats = get_role_statistics(cur)
        print(f"역할별 통계: {stats}")

        # 2. 기본 역할별 검색 테스트
        print("\n1. 기본 역할별 검색:")
        for role in ['user', 'system', 'test']:
            results = search_by_role_dict(cur, role, limit=3)
            print(f"  {role} 역할: {len(results)}개")
            if results:
                print(f"    샘플: {results[0]['text'][:50]}...")

        # 3. 통합 검색 테스트
        print("\n2. 통합 검색:")
        unified = search_roles_unified(cur, ['user', 'system'], limit_per_role=2)
        for role, results in unified.items():
            print(f"  {role}: {len(results)}개")

        # 4. 고급 검색 테스트
        print("\n3. 고급 검색 (최근 7일):")
        recent_user = search_by_role_advanced(cur, 'user', days=7, limit=3)
        print(f"  최근 사용자 메시지: {len(recent_user)}개")

        # 5. 키워드 검색 테스트
        print("\n4. 키워드 검색:")
        velos_results = search_by_role_with_keyword(cur, 'system', 'VELOS', limit=3)
        print(f"  시스템 VELOS 관련: {len(velos_results)}개")

        # 6. 정규화된 쿼리 검색 테스트
        print("\n5. 정규화된 쿼리 검색:")
        from_query = "from:system VELOS"
        normalized_results = search_with_normalized_query(cur, from_query, limit=3)
        print(f"  '{from_query}' -> {len(normalized_results)}개 결과")

        # 7. 쿼리 정규화 테스트
        print("\n6. 쿼리 정규화 테스트:")
        test_queries = [
            "from:user test",
            "from:system VELOS",
            "from:test sample"
        ]
        for q in test_queries:
            normalized = normalize_query(q)
            print(f"  '{q}' -> '{normalized}'")

        conn.close()
        print("\n✅ 모든 테스트 완료")

    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        exit(1)

