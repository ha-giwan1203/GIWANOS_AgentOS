#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""본체 오류리스트 시트 정적 박기 단독 진입점.

build_formula_version 풀 재빌드 후 COM 정적 박기 단계만 실패한 경우,
또는 EXCEL.EXE 충돌로 1회만 다시 시도하고 싶을 때 사용.

사전 조건: EXCEL.EXE 사용자 인스턴스 모두 닫기.
사용법:
    python populate_err_list_only.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

from openpyxl import load_workbook
from _pipeline_config import BASE_DIR, MONTH, LINE_ORDER

_m_int = int(MONTH) + 1
if _m_int > 12:
    _m_int -= 12
folder = f'{_m_int:02d}월'
output = os.path.join(BASE_DIR, folder, f'정산_수식버전_{MONTH}월.xlsx')

if not os.path.exists(output):
    print(f'[ERROR] 본체 미존재: {output}')
    sys.exit(1)

print(f'대상: {output}')

# 라인시트 sum_row 추출 (build_formula_version과 동일 컨벤션 — '합계' 셀)
wb = load_workbook(output, data_only=False, read_only=False)
line_summaries = {}
lines = []
for lc in LINE_ORDER:
    if lc not in wb.sheetnames:
        continue
    lines.append(lc)
    ws = wb[lc]
    for r in range(2, ws.max_row + 1):
        if ws.cell(r, 1).value == '합계':
            line_summaries[lc] = r
            break
wb.close()

print(f'line_summaries: {line_summaries}')

# build_formula_version에서 함수만 import (main 블록 실행 회피 위해 직접 정의 일부 복사 X — module side-effect 감수)
# 함수 단독 호출이 필요 → import 시 main 블록 실행됨. side-effect 최소화 위해 별도 모듈로 분리하는 게 이상적.
# 임시 우회: build_formula_version 안의 populate_error_list_static을 별도 함수로 추출했다면 import OK.
# 현재는 module-level 풀 빌드가 트리거됨. 그래서 직접 함수 정의 import는 불가.
# → 사용자는 EXCEL 닫고 `python build_formula_version.py` 재호출 권고.

print('현 시점 단독 호출 불가 — build_formula_version main 블록과 함수가 한 파일이라 import만으로도 풀 빌드 트리거.')
print('해결: EXCEL.EXE 인스턴스 닫은 후 `python build_formula_version.py` 재호출.')
sys.exit(2)
