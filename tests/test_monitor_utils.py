#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
monitor_utils.py 테스트 스크립트
"""

import pandas as pd
import sys
from pathlib import Path

# 모듈 경로 추가
sys.path.append(str(Path(__file__).parent / "modules"))

from monitor_utils import with_prefix, _safe_attach

def test_basic_functionality():
    """기본 기능 테스트"""
    print("=== monitor_utils.py 테스트 ===\n")
    
    # 기본 데이터 준비
    left = pd.DataFrame({"id": [1, 2, 3], "score": [90, 80, 70]})
    right = pd.DataFrame({"id": [1, 2, 3], "p": [0.1, 0.2, 0.3], "q": [5, 6, 7]})
    
    print("1️⃣ 우측 컬럼에 prefix 붙여서 조인")
    out = _safe_attach(left, right, on="id", prefix="model", conflict="suffix")
    print("결과:")
    print(out)
    print(f"컬럼: {list(out.columns)}\n")
    
    # 2) 인덱스 정렬이 같은 경우, 키 없이 바로 붙이기
    print("2️⃣ Series 병합 (인덱스 기준)")
    s = pd.Series([True, False, True], name="flag")
    out2 = _safe_attach(left, s, prefix="meta")
    print("결과:")
    print(out2)
    print(f"컬럼: {list(out2.columns)}\n")
    
    # 3) with_prefix만 단독 사용
    print("3️⃣ with_prefix 단독 사용")
    pref = with_prefix(right.drop(columns=["id"]), "r")
    print("결과:")
    print(pref)
    print(f"컬럼: {list(pref.columns)}\n")
    
    # 추가 테스트
    print("4️⃣ 충돌 해결 정책 테스트")
    conflict_df = pd.DataFrame({"id": [1, 2], "name": ["Alice", "Bob"]})
    conflict_other = pd.DataFrame({"id": [1, 2], "name": ["Alice2", "Bob2"], "age": [25, 30]})
    
    # suffix 정책
    result_suffix = _safe_attach(conflict_df, conflict_other, on="id", prefix="right", conflict="suffix")
    print("suffix 정책 결과:")
    print(result_suffix)
    print(f"컬럼: {list(result_suffix.columns)}\n")
    
    # keep_left 정책
    result_left = _safe_attach(conflict_df, conflict_other, on="id", prefix="right", conflict="keep_left")
    print("keep_left 정책 결과:")
    print(result_left)
    print(f"컬럼: {list(result_left.columns)}\n")
    
    # keep_right 정책
    result_right = _safe_attach(conflict_df, conflict_other, on="id", prefix="right", conflict="keep_right")
    print("keep_right 정책 결과:")
    print(result_right)
    print(f"컬럼: {list(result_right.columns)}\n")

if __name__ == "__main__":
    test_basic_functionality()

