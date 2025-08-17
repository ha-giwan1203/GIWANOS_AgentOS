#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
monitor_utils.py 빠른 자가 테스트 (복붙용)
"""

import pandas as pd
import sys
from pathlib import Path

# 모듈 경로 추가
sys.path.append(str(Path(__file__).parent / "modules"))

from modules.monitor_utils import with_prefix, _safe_attach

def quick_test():
    """빠른 자가 테스트"""
    print("=== monitor_utils.py 빠른 자가 테스트 ===\n")

    left = pd.DataFrame({"id": [1, 2, 3], "score": [90, 80, 70]})
    right = pd.DataFrame({"id": [1, 2, 3], "p": [0.1, 0.2, 0.3], "q": [5, 6, 7]})

    print("📋 기본 데이터:")
    print("left:")
    print(left)
    print("\nright:")
    print(right)
    print()

    # 1) 키 조인 + 프리픽스
    print("1️⃣ 키 조인 + 프리픽스:")
    out = _safe_attach(left, right, on="id", prefix="model", conflict="suffix")
    print("결과:")
    print(out)
    print(f"컬럼: {out.columns.tolist()}")  # ['id','score','model.p','model.q']
    print()

    # 2) 인덱스 기준 붙이기(Series)
    print("2️⃣ 인덱스 기준 붙이기(Series):")
    s = pd.Series([True, False, True], name="flag")
    out2 = _safe_attach(left, s, prefix="meta")
    print("결과:")
    print(out2)
    print(f"컬럼: {out2.columns.tolist()}")  # ['id','score','meta.flag']
    print()

    # 3) 프리픽스만 단독
    print("3️⃣ 프리픽스만 단독:")
    prefixed = with_prefix(right.drop(columns=["id"]), "r")
    print("결과:")
    print(prefixed)
    print(f"컬럼: {prefixed.columns.tolist()}")  # ['r.p','r.q']
    print()

    # 추가 테스트: 충돌 해결
    print("4️⃣ 충돌 해결 테스트:")
    conflict_df = pd.DataFrame({"id": [1, 2], "name": ["Alice", "Bob"]})
    conflict_other = pd.DataFrame({"id": [1, 2], "name": ["Alice2", "Bob2"], "age": [25, 30]})

    # suffix 정책
    result = _safe_attach(conflict_df, conflict_other, on="id", prefix="right", conflict="suffix")
    print("suffix 정책 결과:")
    print(result)
    print(f"컬럼: {result.columns.tolist()}")
    print()

    print("✅ 모든 테스트 완료!")


if __name__ == "__main__":
    quick_test()
