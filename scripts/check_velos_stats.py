# [ACTIVE] VELOS 시스템 통계 확인 - 시스템 통계 분석 스크립트
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VELOS 운영 철학 선언문: 파일명은 절대 변경하지 않는다. 수정 시 자가 검증을 포함하고,
실행 결과를 기록하며, 경로/구조는 불변으로 유지한다. 실패는 로깅하고 자동 복구를
시도한다.

VELOS 시스템 통계 확인 스크립트
전체 시스템의 상태와 통계를 확인합니다.
"""

import os
import sys
from pathlib import Path

# 모듈 경로 추가
sys.path.append(str(Path(__file__).parent.parent))

try:
    from modules.memory.router.query_router import get_cache_stats
    from modules.memory.cache.velos_cache_adapter import VelosCachedMemoryAdapter
except ImportError:
    print("⚠️ 일부 모듈을 불러올 수 없습니다. 기본 통계만 확인합니다.")


def _env(key, default=None):
    """환경 변수 로드 (ENV > configs/settings.yaml > 기본값)"""
    import yaml

    # 1. 환경 변수 확인
    value = os.getenv(key)
    if value:
        return value

    # 2. configs/settings.yaml 확인
    try:
        config_path = (Path(__file__).parent.parent / 'configs' /
                      'settings.yaml')
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                if config and key in config:
                    return str(config[key])
    except Exception:
        pass

    # 3. 기본값 반환
    return default or 'C:/giwanos'


def check_basic_stats():
    """기본 DB 통계 확인"""
    import sqlite3

    db_path = _env('VELOS_DB', 'C:/giwanos/data/velos.db')

    print(f"VELOS DB 경로: {db_path}")

    if not os.path.exists(db_path):
        print("❌ DB 파일이 존재하지 않습니다")
        return

    try:
        with sqlite3.connect(db_path) as conn:
            # 기본 통계 (개선된 패턴)
            total_mem = conn.execute("SELECT COUNT(*) FROM memory").fetchone()[0]
            total_fts = conn.execute("SELECT COUNT(*) FROM memory_fts").fetchone()[0]
            print(f"VELOS 메모리 시스템 종합 통계:")
            print(f"  총 레코드: {total_mem}개")
            print(f"  FTS 인덱스: {total_fts}개")

            # 뷰 확인
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='view'")
            views = [row[0] for row in cursor.fetchall()]
            print(f"호환성 뷰: {views}")

            # memory_text 뷰 테스트
            if 'memory_text' in views:
                cursor = conn.execute("SELECT COUNT(*) FROM memory_text")
                view_count = cursor.fetchone()[0]
                print(f"memory_text 뷰 레코드: {view_count}")

                # 뷰 샘플 데이터 확인
                cursor = conn.execute("""
                    SELECT id, substr(text_norm, 1, 40) as preview
                    FROM memory_text
                    ORDER BY ts DESC
                    LIMIT 2
                """)
                samples = cursor.fetchall()
                print("뷰 샘플:")
                for row in samples:
                    print(f"  ID {row[0]}: {row[1]}...")

            # 최근 데이터 확인 (새로운 패턴)
            cursor = conn.execute("""
                SELECT ts, role, substr(text, 1, 50) as preview
                FROM memory_roles
                ORDER BY ts DESC
                LIMIT 3
            """)
            recent = cursor.fetchall()
            print(f"\n최근 데이터 ({len(recent)}개):")
            for row in recent:
                print(f"  {row[0]}: {row[1]} - {row[2]}...")

            # 역할별 통계 (새로운 패턴)
            print(f"\n역할별 통계:")
            roles = ['user', 'system', 'test']
            for role in roles:
                cursor = conn.execute("SELECT COUNT(*) FROM memory_roles WHERE role=?", (role,))
                count = cursor.fetchone()[0]
                print(f"  {role} 역할: {count}개")

    except Exception as e:
        print(f"❌ 기본 통계 확인 오류: {e}")


def check_advanced_stats():
    """고급 통계 확인 (캐시 어댑터 사용)"""
    try:
        adapter = VelosCachedMemoryAdapter()
        stats = adapter.get_stats_enhanced()

        print(f"\n=== 고급 통계 ===")

        # 안전한 통계 추출 패턴 (개선된 버전)
        total = (
            stats.get("total_records")
            or stats.get("memory", {}).get("db_records")
            or stats.get("memory", {}).get("records")
            or 0
        )
        fts_count = (
            stats.get("fts_records")
            or stats.get("fts", {}).get("records")
            or stats.get("memory", {}).get("fts_records")
            or 0
        )
        recent_days = stats.get("recent_days", 7)
        recent_records = (
            stats.get("recent_records")
            or stats.get("memory", {}).get("recent_records")
            or 0
        )

        print(f"총 레코드: {total:,}")
        print(f"FTS 인덱스: {fts_count:,}")
        print(f"최근 {recent_days}일: {recent_records:,}")

        # 캐시 통계
        cache_stats = adapter.get_cache_stats()
        print(f"\n=== 캐시 통계 ===")
        for cache_name, stats in cache_stats.items():
            # 안전한 캐시 통계 추출
            hits = stats.get('hits', 0)
            misses = stats.get('misses', 0)
            sets = stats.get('sets', 0)
            evictions = stats.get('evictions', 0)

            hit_rate = (hits / (hits + misses) * 100) if (hits + misses) > 0 else 0
            print(f"{cache_name}:")
            print(f"  히트: {hits}, 미스: {misses}, 히트율: {hit_rate:.1f}%")
            print(f"  설정: {sets}, 제거: {evictions}")

    except Exception as e:
        print(f"⚠️ 고급 통계 확인 실패: {e}")


def check_query_cache_stats():
    """쿼리 캐시 통계 확인"""
    try:
        cache_stats = get_cache_stats()
        print(f"\n=== 쿼리 캐시 통계 ===")
        hits = cache_stats.get('hits', 0)
        misses = cache_stats.get('misses', 0)
        total = hits + misses
        hit_rate = (hits / total * 100) if total > 0 else 0

        print(f"총 쿼리: {total}")
        print(f"캐시 히트: {hits}")
        print(f"캐시 미스: {misses}")
        print(f"히트율: {hit_rate:.1f}%")

    except Exception as e:
        print(f"⚠️ 쿼리 캐시 통계 확인 실패: {e}")


if __name__ == "__main__":
    print("VELOS 시스템 통계 확인 시작...")

    check_basic_stats()
    check_advanced_stats()
    check_query_cache_stats()

    print("\n✅ 통계 확인 완료")
