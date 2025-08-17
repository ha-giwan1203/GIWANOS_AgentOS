# VELOS 운영 철학 선언문: 파일명은 절대 변경하지 않는다. 수정 시 자가 검증을 포함하고,
# 실행 결과를 기록하며, 경로/구조는 불변으로 유지한다. 실패는 로깅하고 자동 복구를 시도한다.

"""
통합된 역할별 쿼리 예제

기존의 분리된 user_rows, system_rows 쿼리를 통합된 쿼리로 교체하는 방법을 보여줍니다.
"""

import os
import sys
import sqlite3
from typing import Dict, List, Any

# VELOS 루트 경로 설정
VELOS_ROOT = os.getenv('VELOS_ROOT', 'C:/giwanos')
sys.path.append(VELOS_ROOT)

from modules.core.memory_adapter import MemoryAdapter


def old_separated_query_example():
    """기존의 분리된 쿼리 방식 (교체 대상)"""
    db_path = os.path.join(VELOS_ROOT, "data", "velos.db")

    if not os.path.exists(db_path):
        print("❌ 데이터베이스 파일이 존재하지 않습니다.")
        return

    try:
        conn = sqlite3.connect(db_path, timeout=5)
        cur = conn.cursor()

        # 기존 방식: 두 번의 별도 쿼리
        user_rows = cur.execute("""
            SELECT id, ts, role, source, text
            FROM memory_roles
            WHERE role='user'
            ORDER BY ts DESC
            LIMIT 10
        """).fetchall()

        system_rows = cur.execute("""
            SELECT id, ts, role, source, text
            FROM memory_roles
            WHERE role='system'
            ORDER BY ts DESC
            LIMIT 10
        """).fetchall()

        print(f"기존 방식 결과:")
        print(f"  User 역할: {len(user_rows)}개")
        print(f"  System 역할: {len(system_rows)}개")

        conn.close()

    except Exception as e:
        print(f"❌ 기존 쿼리 실행 오류: {e}")


def new_unified_query_example():
    """새로운 통합된 쿼리 방식 (개선된 방식)"""
    try:
        adapter = MemoryAdapter()

        # 새로운 방식: 한 번의 통합된 쿼리
        result = adapter.get_roles_unified(limit=10)

        user_rows = result["user"]
        system_rows = result["system"]

        print(f"\n새로운 통합 방식 결과:")
        print(f"  User 역할: {len(user_rows)}개")
        print(f"  System 역할: {len(system_rows)}개")

        # 샘플 데이터 출력
        if user_rows:
            print(f"\n최근 User 메시지 샘플:")
            for row in user_rows[:3]:
                print(f"  [{row['ts']}] {row['text'][:50]}...")

        if system_rows:
            print(f"\n최근 System 메시지 샘플:")
            for row in system_rows[:3]:
                print(f"  [{row['ts']}] {row['text'][:50]}...")

    except Exception as e:
        print(f"❌ 새로운 쿼리 실행 오류: {e}")


def direct_sql_unified_query():
    """직접 SQL을 사용한 통합 쿼리 방식"""
    db_path = os.path.join(VELOS_ROOT, "data", "velos.db")

    if not os.path.exists(db_path):
        print("❌ 데이터베이스 파일이 존재하지 않습니다.")
        return

    try:
        conn = sqlite3.connect(db_path, timeout=5)
        cur = conn.cursor()

        # 통합된 쿼리로 한 번에 조회
        unified_rows = cur.execute("""
            SELECT id, ts, role, source, text
            FROM memory_roles
            WHERE role IN ('user', 'system')
            ORDER BY ts DESC
            LIMIT 20
        """).fetchall()

        # 역할별로 분류
        user_rows = [row for row in unified_rows if row[2] == 'user'][:10]
        system_rows = [row for row in unified_rows if row[2] == 'system'][:10]

        print(f"\n직접 SQL 통합 방식 결과:")
        print(f"  User 역할: {len(user_rows)}개")
        print(f"  System 역할: {len(system_rows)}개")

        conn.close()

    except Exception as e:
        print(f"❌ 직접 SQL 쿼리 실행 오류: {e}")


def performance_comparison():
    """성능 비교 테스트"""
    import time

    db_path = os.path.join(VELOS_ROOT, "data", "velos.db")

    if not os.path.exists(db_path):
        print("❌ 데이터베이스 파일이 존재하지 않습니다.")
        return

    try:
        conn = sqlite3.connect(db_path, timeout=5)
        cur = conn.cursor()

        # 기존 방식 시간 측정
        start_time = time.time()
        for _ in range(10):
            cur.execute("""
                SELECT id, ts, role, source, text
                FROM memory_roles
                WHERE role='user'
                ORDER BY ts DESC
                LIMIT 10
            """).fetchall()

            cur.execute("""
                SELECT id, ts, role, source, text
                FROM memory_roles
                WHERE role='system'
                ORDER BY ts DESC
                LIMIT 10
            """).fetchall()
        old_time = time.time() - start_time

        # 새로운 방식 시간 측정
        start_time = time.time()
        for _ in range(10):
            cur.execute("""
                SELECT id, ts, role, source, text
                FROM memory_roles
                WHERE role IN ('user', 'system')
                ORDER BY ts DESC
                LIMIT 20
            """).fetchall()
        new_time = time.time() - start_time

        print(f"\n성능 비교 (10회 반복):")
        print(f"  기존 방식: {old_time:.4f}초")
        print(f"  새로운 방식: {new_time:.4f}초")
        print(f"  성능 향상: {((old_time - new_time) / old_time * 100):.1f}%")

        conn.close()

    except Exception as e:
        print(f"❌ 성능 비교 오류: {e}")


if __name__ == "__main__":
    print("=== VELOS 통합 역할별 쿼리 예제 ===\n")

    # 1. 기존 방식 예제
    old_separated_query_example()

    # 2. 새로운 방식 예제
    new_unified_query_example()

    # 3. 직접 SQL 방식 예제
    direct_sql_unified_query()

    # 4. 성능 비교
    performance_comparison()

    print("\n=== 사용법 요약 ===")
    print("기존 방식 (교체 대상):")
    print("  user_rows = cur.execute('SELECT ... WHERE role=\"user\"')")
    print("  system_rows = cur.execute('SELECT ... WHERE role=\"system\"')")
    print("\n새로운 방식 (권장):")
    print("  result = adapter.get_roles_unified(limit=10)")
    print("  user_rows = result['user']")
    print("  system_rows = result['system']")
    print("\n또는 직접 SQL:")
    print("  unified_rows = cur.execute('SELECT ... WHERE role IN (\"user\", \"system\")')")
