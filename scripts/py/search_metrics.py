# [ACTIVE] VELOS 운영 철학 선언문
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.

검색 품질 메트릭 측정 스크립트
search.qps, search.latency_p50, fts.rebuild_count를 측정합니다.
"""

import os
import sqlite3
import time
import statistics
from typing import Dict, List, Tuple


def measure_search_metrics() -> Dict[str, float]:
    """검색 품질 메트릭을 측정합니다."""
    db = os.getenv("VELOS_DB_PATH", r"C:\giwanos\data\velos.db")
    
    if not os.path.exists(db):
        print(f"ERROR: 데이터베이스 파일이 존재하지 않습니다: {db}")
        return {}
    
    try:
        con = sqlite3.connect(db)
        cur = con.cursor()
        
        # 1. search.qps 측정 (초당 검색 쿼리 수)
        print("검색 QPS 측정 중...")
        test_queries = ["test", "velos", "system", "user", "memory"]
        latencies = []
        
        for _ in range(50):  # 50회 측정
            start_time = time.time()
            cur.execute("""
                SELECT COUNT(*) FROM memory_fts 
                WHERE memory_fts MATCH ? LIMIT 10
            """, (test_queries[_ % len(test_queries)],))
            end_time = time.time()
            latencies.append((end_time - start_time) * 1000)  # ms로 변환
        
        # QPS 계산 (1초 / 평균 응답시간)
        avg_latency_ms = statistics.mean(latencies)
        qps = 1000 / avg_latency_ms if avg_latency_ms > 0 else 0
        
        # P50 지연시간
        latency_p50 = statistics.median(latencies)
        
        # 2. fts.rebuild_count 측정
        print("FTS 재색인 횟수 확인 중...")
        rebuild_count = 0
        try:
            # 최근 7일간의 재색인 이벤트 확인
            cur.execute("""
                SELECT COUNT(*) FROM memory 
                WHERE role = 'system' AND insight LIKE '%rebuild%'
                AND ts >= strftime('%s', 'now', '-7 days')
            """)
            rebuild_count = cur.fetchone()[0]
        except Exception:
            rebuild_count = 0
        
        con.close()
        
        metrics = {
            "search.qps": round(qps, 2),
            "search.latency_p50": round(latency_p50, 2),
            "fts.rebuild_count": rebuild_count
        }
        
        print("=== 검색 품질 메트릭 ===")
        print(f"search.qps: {metrics['search.qps']}/s")
        print(f"search.latency_p50: {metrics['search.latency_p50']}ms")
        print(f"fts.rebuild_count: {metrics['fts.rebuild_count']}/7days")
        
        # 기준값 대비 평가
        print("\n=== 기준값 대비 평가 ===")
        if metrics['search.qps'] > 1000:
            print("✅ search.qps: 기준값(1000/s) 초과")
        else:
            print("⚠️ search.qps: 기준값(1000/s) 미달")
            
        if metrics['search.latency_p50'] < 50:
            print("✅ search.latency_p50: 기준값(50ms) 미만")
        else:
            print("⚠️ search.latency_p50: 기준값(50ms) 초과")
            
        if metrics['fts.rebuild_count'] < 1:
            print("✅ fts.rebuild_count: 기준값(1/주) 미만")
        else:
            print("⚠️ fts.rebuild_count: 기준값(1/주) 초과")
        
        return metrics
        
    except Exception as e:
        print(f"ERROR: 메트릭 측정 실패: {e}")
        return {}


if __name__ == "__main__":
    metrics = measure_search_metrics()
    if metrics:
        print(f"\n메트릭 측정 완료: {metrics}")
    else:
        print("메트릭 측정 실패")
        exit(1)


