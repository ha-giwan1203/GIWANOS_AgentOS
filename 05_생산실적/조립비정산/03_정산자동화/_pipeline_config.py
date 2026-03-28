#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
정산 파이프라인 공통 설정
모든 step 스크립트에서 import해서 사용한다.

사용법:
    from _pipeline_config import *
"""

import os

# ============================================================
# 기본 경로 (월별로만 OUTPUT_FILE 변경)
# ============================================================
BASE_DIR     = r'C:\Users\User\Desktop\업무리스트\05_생산실적\조립비정산'
CACHE_DIR    = os.path.join(os.path.dirname(__file__), '_cache')

MASTER_FILE  = os.path.join(BASE_DIR, '01_기준정보', '기준정보_라인별정리_최종_V1_20260316.xlsx')
GERP_FILE    = os.path.join(BASE_DIR, '04_실적데이터', 'GERP_실적현황_20260311.xlsx')
OLDERP_FILE  = os.path.join(BASE_DIR, '04_실적데이터', '구ERP_실적현황_20260311.xlsx')
OUTPUT_FILE  = os.path.join(BASE_DIR, '정산결과_03월.xlsx')   # ← 월 바꿀 때 수정

MONTH        = '03'
VENDOR_CODE  = '0109'
SP3M3_NIGHT_PRICE = 170   # SP3M3 야간 고정단가(원)
SP3M3_MODULE_FILE = os.path.join(os.path.dirname(os.path.dirname(BASE_DIR)), '03_품번관리', '초물관리', 'SP3M3_모듈품번_최신.xlsx')  # RSP→품번 매핑 (1차)
LINE_ASSIGN_FILE  = os.path.join(os.path.dirname(os.path.dirname(BASE_DIR)), '10_라인배치', '라인배치_ENDPART라인배정.xlsx')  # RSP→품번 보조매핑

# ============================================================
# 라인 정보
# ============================================================
LINE_ORDER = [
    'SD9A01', 'SP3M3', 'WAMAS01', 'WABAS01',
    'ANAAS04', 'DRAAS11', 'WASAS01', 'HCAMS02', 'HASMS02', 'ISAMS03',
]

LINE_INFO = {
    'SD9A01':  {'name': '아우터',        'type': 'OUTER', 'has_night': True},
    'SP3M3':   {'name': '메인',          'type': 'MAIN',  'has_night': True},
    'WAMAS01': {'name': '웨빙 ASSY',     'type': 'SUB',   'has_night': False},
    'WABAS01': {'name': '웨빙 스토퍼',   'type': 'SUB',   'has_night': False},
    'ANAAS04': {'name': '앵커',          'type': 'SUB',   'has_night': False},
    'DRAAS11': {'name': '디링',          'type': 'SUB',   'has_night': False},
    'WASAS01': {'name': '웨빙 스토퍼2',  'type': 'SUB',   'has_night': False},
    'HCAMS02': {'name': '홀더 CLR ASSY', 'type': 'SUB',   'has_night': False},
    'HASMS02': {'name': '홀더센스 ASSY', 'type': 'SUB',   'has_night': False},
    'ISAMS03': {'name': '이너센스 ASSY', 'type': 'SUB',   'has_night': False},
}

# 구ERP 라인코드 → GERP 라인코드
OLD_ERP_LINE_MAP = {
    'TD9':    'SD9A01',
    'D9N6':   'SD9A01',
    'SP3S03': 'SP3M3',
}

# ============================================================
# GERP 컬럼 인덱스 (0-based, header=None, data from row 2)
# ============================================================
GERP_COL = {
    'line':       2,
    'product_no': 6,
    'usage':      10,
    'assy_part':  11,   # 조립품번
    'shift':      13,   # '정상'=주간, '추가'=야간
    'qty':        14,
    'unit_price': 15,
    'amount':     16,
    'vendor_cd':  20,
}

# ============================================================
# 구ERP 컬럼 인덱스 (0-based, header=None, data from row 2)
# ============================================================
OLDERP_COL = {
    'vendor':    2,
    'part_no':   4,
    'qty':       5,
    'line_code': 7,
    'lot_no':    10,  # 끝자리 B=야간, 나머지=주간
    'unit_cost': 11,
    'amount':    12,
}

# ============================================================
# 기준정보 컬럼 인덱스 (0-based, header row=2, data from row 3)
# ============================================================
MASTER_COL = {
    'part_no':    0,
    'vendor_cd':  1,
    'line_code':  2,
    'assy_part':  3,
    'usage':      4,
    'price_type': 5,
    'price':      6,
    'vtype':      7,
}

# ============================================================
# JSON 캐시 파일 경로
# ============================================================
CACHE_STEP1 = os.path.join(CACHE_DIR, 'step1_validation.json')
CACHE_STEP2 = os.path.join(CACHE_DIR, 'step2_gerp.json')
CACHE_STEP3 = os.path.join(CACHE_DIR, 'step3_olderp.json')
CACHE_STEP4 = os.path.join(CACHE_DIR, 'step4_matched.json')
CACHE_STEP5 = os.path.join(CACHE_DIR, 'step5_settlement.json')

os.makedirs(CACHE_DIR, exist_ok=True)
