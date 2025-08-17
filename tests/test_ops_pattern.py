#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_safe_attach + with_prefix 패턴 테스트
"""

import pandas as pd
import sys
from pathlib import Path

# 모듈 경로 추가
sys.path.append(str(Path(__file__).parent / "modules"))

from monitor_utils import _safe_attach, with_prefix


def make_ops_df(base_df):
    """예시: base_df에 대응하는 operations DataFrame 생성"""
    # 실제로는 base_df의 각 행에 대한 작업 정보를 생성
    ops_data = {
        '보기': [f"view_{i}" for i in range(len(base_df))],
        '다운': [f"download_{i}" for i in range(len(base_df))],
        '링크': [f"link_{i}" for i in range(len(base_df))],
        '편집': [f"edit_{i}" for i in range(len(base_df))],
        '삭제': [f"delete_{i}" for i in range(len(base_df))]
    }
    return pd.DataFrame(ops_data, index=base_df.index)


def test_ops_pattern():
    """깔끔한 병합 패턴 테스트"""
    print("=== _safe_attach + with_prefix 패턴 테스트 ===\n")
    
    # 기본 데이터 준비
    base_df = pd.DataFrame({
        'id': [1, 2, 3, 4, 5],
        'name': ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve'],
        'score': [85, 92, 78, 95, 88]
    })
    
    print("📋 기본 데이터:")
    print(base_df)
    print(f"컬럼: {list(base_df.columns)}\n")
    
    # 붙일 오른쪽 데이터(여러 컬럼 가능)
    ops = make_ops_df(base_df)
    print("🔧 Operations 데이터:")
    print(ops)
    print(f"컬럼: {list(ops.columns)}\n")
    
    # 한 번에 깔끔하게 병합 (인덱스 기준 붙이기)
    print("🔄 병합 결과:")
    base_df = _safe_attach(base_df, with_prefix(ops, "ops"))
    print(base_df)
    print(f"최종 컬럼: {list(base_df.columns)}\n")
    
    # 추가 패턴 테스트
    print("📊 추가 패턴 테스트:")
    
    # 1. 여러 단계 병합
    print("1️⃣ 여러 단계 병합:")
    df1 = pd.DataFrame({'id': [1, 2, 3], 'name': ['A', 'B', 'C']})
    
    # 첫 번째 병합
    stats = pd.DataFrame({'count': [10, 20, 30], 'avg': [1.5, 2.5, 3.5]}, index=df1.index)
    df1 = _safe_attach(df1, with_prefix(stats, "통계"))
    
    # 두 번째 병합
    flags = pd.Series([True, False, True], name="활성", index=df1.index)
    df1 = _safe_attach(df1, with_prefix(flags.to_frame(), "상태"))
    
    print(df1)
    print(f"컬럼: {list(df1.columns)}\n")
    
    # 2. 충돌 해결 패턴
    print("2️⃣ 충돌 해결 패턴:")
    df2 = pd.DataFrame({'id': [1, 2], 'name': ['X', 'Y']})
    conflict_data = pd.DataFrame({'id': [1, 2], 'name': ['X2', 'Y2'], 'value': [100, 200]})
    
    # suffix로 충돌 해결
    result = _safe_attach(df2, with_prefix(conflict_data, "추가"), on="id", conflict="suffix")
    print(result)
    print(f"컬럼: {list(result.columns)}\n")
    
    # 3. 복합 prefix 패턴
    print("3️⃣ 복합 prefix 패턴:")
    df3 = pd.DataFrame({'id': [1, 2, 3], 'type': ['A', 'B', 'A']})
    
    # 서로 다른 prefix로 여러 데이터 병합
    user_data = pd.DataFrame({'role': ['admin', 'user', 'guest'], 'level': [3, 1, 0]}, index=df3.index)
    system_data = pd.DataFrame({'status': ['active', 'inactive', 'active'], 'priority': [1, 2, 1]}, index=df3.index)
    
    df3 = _safe_attach(df3, with_prefix(user_data, "사용자"))
    df3 = _safe_attach(df3, with_prefix(system_data, "시스템"))
    
    print(df3)
    print(f"컬럼: {list(df3.columns)}\n")


if __name__ == "__main__":
    test_ops_pattern()

