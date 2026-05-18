#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
조립비 정산 오류유형 1차 통합 분류 (2026-05-18)

캡처 매트릭스(품번/기준정보 등록 상태) + 기존 빌더 8유형(데이터 차이)을 합친 통합 사전.

1차 분류 — 품번/기준정보 매트릭스 (M1~M6):
  M1 GERP 품번누락   구ERP O / GERP X / 마스터 O  → "GERP 신규등록필요"        완성품라인 한정
  M2 GERP 품번누락   구ERP O / GERP X / 마스터 X  → "GERP·기준정보 등록필요"   완성품라인 한정
  M3 라인코드 누락   구ERP O / GERP 품번O 라인코드X / 마스터 O → "라인코드 추가필요"  전라인 (step4 unmatched)
  M4 라인확인 필요   구ERP X / GERP O / 마스터 X  → "라인+기준정보 확인필요"   전라인
  M5 라인확인 필요   구ERP X / GERP O / 마스터 O  → "라인품번 확인필요"        전라인
  M6 기준정보 누락   구ERP O / GERP O / 마스터 X  → "기준정보 등록필요"        전라인

2차 분류 — 3 품번 모두 존재 + 데이터 차이 (D0~D4):
  D0 정상         차이 0원
  D1 수량차이     수량만 다름
  D2 단가차이     단가만 다름
  D3 단가+수량    수량·단가 모두 다름
  D4 정산차이     수량·단가 동일, 금액만 다름 (야간계산식 차이 등)

특수 — 분류와 직교 (제외사유):
  X1 정합인정(다중단가분배)  동일품번 마스터 2+ 단가 분배 정상
  X2 이관품번                OVK·SVM·X9000·X9500 등
  X3 웨빙재작업              89830R1200NNB 등
  공란                       그 외 (받을금액 청구 대상)

받을금액 룰:
  recv_amt = abs(amt_diff) if excl_reason == "" else 0
"""

# ──────────────────────────────────────────────────────────────
# 표준 사전
# ──────────────────────────────────────────────────────────────
ERROR_TYPES = [
    'GERP 품번누락',   # M1, M2
    '라인코드 누락',    # M3
    '라인확인 필요',    # M4, M5
    '기준정보 누락',    # M6
    '정상',            # D0
    '수량차이',        # D1
    '단가차이',        # D2
    '단가+수량',       # D3
    '정산차이',        # D4
]

EXCL_REASONS = [
    '정합인정(다중단가분배)',
    '이관품번',
    '웨빙재작업',
]

# 이관품번 패턴 (사용자 룰)
TRANSFER_PATTERNS = ['X9000', 'X9500']

# 웨빙재작업 품번 (도메인 룰)
WEBBING_REWORK_PARTS = {'89830R1200NNB'}


# ──────────────────────────────────────────────────────────────
# 분류 함수 — Python (step5/7/8 공용)
# ──────────────────────────────────────────────────────────────
def classify_error_type(item, line_group, master_has_pn=None, master_has_price=None):
    """오류유형 + 비고 판정.

    Args:
        item: dict — gerp_day_qty/gerp_ngt_qty/erp_day_qty/erp_ngt_qty/gerp_day_amt/gerp_ngt_amt/erp_day_amt/erp_ngt_amt/price/gerp_price 필드
        line_group: '완성품' / '메인SUB' / '웨빙SUB'
        master_has_pn: 마스터에 품번 존재 여부 (None이면 price>0로 추론)
        master_has_price: 마스터 단가 존재 여부 (None이면 price>0로 추론)

    Returns:
        (err_type, note) 튜플
    """
    g_amt = (item.get('gerp_day_amt') or 0) + (item.get('gerp_ngt_amt') or 0)
    e_amt = (item.get('erp_day_amt') or 0) + (item.get('erp_ngt_amt') or 0)
    g_qty = (item.get('gerp_day_qty') or 0) + (item.get('gerp_ngt_qty') or 0)
    e_qty = (item.get('erp_day_qty') or 0) + (item.get('erp_ngt_qty') or 0)
    price = item.get('price') or 0
    gerp_p = item.get('gerp_price') or 0

    if master_has_price is None:
        master_has_price = (price > 0)
    if master_has_pn is None:
        master_has_pn = master_has_price

    g_exist = (g_amt != 0 or g_qty != 0)
    e_exist = (e_amt != 0 or e_qty != 0)

    # 1차 매트릭스 분류 (품번 존재 유무)
    if not g_exist and e_exist:
        # 구ERP만 실적
        if line_group == '완성품':
            if master_has_pn:
                return ('GERP 품번누락', 'GERP 신규등록필요')
            else:
                return ('GERP 품번누락', 'GERP·기준정보 등록필요')
        else:
            # 메인SUB/웨빙SUB: GERP에 모듈품번(RSP)으로 잡힘 — M1/M2 적용 X
            # 단순 차이로만 표시
            return ('정산차이', 'GERP 모듈품번 매칭 확인')

    if g_exist and not e_exist:
        # GERP만 실적
        if master_has_pn:
            return ('라인확인 필요', '라인품번 확인필요')
        else:
            return ('라인확인 필요', '라인+기준정보 확인필요')

    if g_exist and e_exist and not master_has_price:
        return ('기준정보 누락', '기준정보 등록필요')

    # 2차 데이터 차이 분류 (3 품번 모두 존재 + 마스터 단가 존재)
    qty_diff = g_qty - e_qty
    amt_diff = g_amt - e_amt
    has_qty_diff = (qty_diff != 0)
    has_price_diff = (gerp_p > 0 and price > 0 and price != gerp_p)

    if has_price_diff and has_qty_diff:
        return ('단가+수량', '')
    if has_price_diff:
        return ('단가차이', '')
    if has_qty_diff:
        return ('수량차이', '')
    if amt_diff != 0:
        return ('정산차이', '')
    return ('정상', '')


def classify_exclusion(item, multi_price_pns=None):
    """제외사유 판정. 유형 컬럼과 직교.

    Returns:
        제외사유 문자열 (공란이면 '')
    """
    part_no = str(item.get('part_no') or '')

    if part_no in WEBBING_REWORK_PARTS:
        return '웨빙재작업'

    for pat in TRANSFER_PATTERNS:
        if pat in part_no:
            return '이관품번'

    if multi_price_pns and part_no in multi_price_pns:
        # 다중단가 케이스 — 차이 0이거나 분배 정상 합산일 때만 정합인정
        # (행별 검증은 호출부에서)
        return '정합인정(다중단가분배)'

    return ''


def calc_recv_amt(amt_diff, excl_reason):
    """받을금액 = abs(차이금액) × (제외사유 공란일 때만)."""
    if excl_reason:
        return 0
    return abs(amt_diff or 0)


# ──────────────────────────────────────────────────────────────
# 본체 라인시트 S 컬럼 분류 수식 생성 (build_formula_version용)
# ──────────────────────────────────────────────────────────────
def build_classify_formula(out_r, line_group):
    """라인시트 S 컬럼(19) 분류 수식.

    셀 참조:
      G = 마스터 단가
      I, J = GERP 주간·야간 수량
      K, L = GERP 주간·야간 금액
      M, N = 구ERP 주간·야간 수량
      O, P = 구ERP 주간·야간 금액
      Q = 금액차이
      R = 수량차이
      A = 품번

    분류 우선순위:
      1. 정상 (Q=0)
      2. 다중단가분배(정상) — 분배 합산 잔여 0인 케이스
      3. 1차 매트릭스 (M1/M2/M4/M5/M6)
      4. 2차 데이터 차이 (D1/D2/D3/D4)
    """
    r = out_r
    # 매트릭스 판정 약식
    g_exist = f'(I{r}+J{r}+K{r}+L{r}>0)'
    e_exist = f'(M{r}+N{r}+O{r}+P{r}>0)'
    master_has = f'(G{r}>0)'

    # 완성품라인이면 GERP 품번누락 분기 적용, 그 외엔 정산차이로 묶음
    if line_group == '완성품':
        m1m2 = (
            f'IF(AND(NOT{g_exist},{e_exist}),'
            f'IF({master_has},"GERP 품번누락","GERP 품번누락(마스터X)"),'
        )
    else:
        # 메인SUB/웨빙SUB: GERP X + 구ERP O = 모듈품번 매칭 케이스 → 정산차이로 흡수
        m1m2 = (
            f'IF(AND(NOT{g_exist},{e_exist}),"정산차이",'
        )

    # M4/M5: GERP O / 구ERP X
    m4m5 = (
        f'IF(AND({g_exist},NOT{e_exist}),'
        f'IF({master_has},"라인확인 필요","라인확인 필요(마스터X)"),'
    )
    # M6: 마스터 X (둘 다 실적 있음)
    m6 = (
        f'IF(AND({g_exist},{e_exist},NOT{master_has}),"기준정보 누락",'
    )
    # D1/D2/D3/D4: 차이 종류
    # 단가차이: G(마스터단가) ≠ GERP단가. GERP단가는 시트에 별도 컬럼 없으므로 K/I로 역산
    # 단순화: Q≠0 and R≠0 → 단가+수량 / R≠0 → 수량차이 / Q≠0 → 정산차이
    d_branch = (
        f'IF(AND(R{r}<>0,Q{r}<>0),"단가+수량",'
        f'IF(R{r}<>0,"수량차이",'
        f'IF(Q{r}<>0,"정산차이","정상"))))'
    )

    # 정상 + 다중단가분배 우선
    formula = (
        f'=IF(ROUND(Q{r},0)=0,"정상",'
        f'IF(AND(I{r}+J{r}>0,M{r}+N{r}=0,COUNTIF(A:A,A{r})>1),"다중단가분배(정상)",'
        f'IF(AND(I{r}+J{r}=0,M{r}+N{r}>0,COUNTIF(A:A,A{r})>1),"다중단가분배(정상)",'
        + m1m2 + m4m5 + m6 + d_branch + '))'
    )
    return formula


# ──────────────────────────────────────────────────────────────
# 본체 카테고리 → 사용자 양식 err_type 매핑 (build_formula_version용)
# 라인시트 S 컬럼 cat (엑셀 수식 결과) → 양식 err_type + 비고
# ──────────────────────────────────────────────────────────────
CAT_TO_USER_TYPE = {
    'GERP 품번누락':         ('GERP 품번누락', 'GERP 신규등록필요'),
    'GERP 품번누락(마스터X)': ('GERP 품번누락', 'GERP·기준정보 등록필요'),
    '라인확인 필요':          ('라인확인 필요', '라인품번 확인필요'),
    '라인확인 필요(마스터X)':  ('라인확인 필요', '라인+기준정보 확인필요'),
    '기준정보 누락':          ('기준정보 누락', '기준정보 등록필요'),
    '수량차이':              ('수량차이', ''),
    '단가차이':              ('단가차이', ''),
    '단가+수량':             ('단가+수량', ''),
    '정산차이':              ('정산차이', ''),
}


def map_cat_to_user_type(cat):
    """라인시트 S 컬럼 cat → (err_type, note). 폐기될 옛 cat은 폴백."""
    if cat in CAT_TO_USER_TYPE:
        return CAT_TO_USER_TYPE[cat]
    # 옛 cat 호환 (단계적 폐기)
    LEGACY = {
        'GERP만(구ERP등록필요)':       ('라인확인 필요', '라인품번 확인필요'),
        'GERP만(마스터+구ERP등록필요)': ('라인확인 필요', '라인+기준정보 확인필요'),
        '구ERP만(GERP등록필요)':       ('GERP 품번누락', 'GERP 신규등록필요'),
        '기준단가누락':                ('기준정보 누락', '기준정보 등록필요'),
        '수량차이(중복확인필요)':       ('수량차이', ''),
        '수량차이(다중단가합산검증)':    ('수량차이', '다중단가합산검증'),
        '단가차이/기타':                ('정산차이', ''),
        'Usage차이':                   ('수량차이', 'Usage차이'),
    }
    if cat in LEGACY:
        return LEGACY[cat]
    return (cat, '')


# ──────────────────────────────────────────────────────────────
# 유형별 색상 (UI 일관성)
# ──────────────────────────────────────────────────────────────
TYPE_COLORS = {
    'GERP 품번누락':  'FFF2CC',
    '라인코드 누락':   'FCE4D6',
    '라인확인 필요':   'D6E4F7',
    '기준정보 누락':   'F4CCCC',
    '정상':           'E2EFDA',
    '수량차이':       'FCE5CD',
    '단가차이':       'D9EAD3',
    '단가+수량':      'F9CB9C',
    '정산차이':       'E8D5F5',
}

# 사용자 양식 정렬 순서
TYPE_ORDER = [
    'GERP 품번누락',
    '라인코드 누락',
    '라인확인 필요',
    '기준정보 누락',
    '수량차이',
    '단가차이',
    '단가+수량',
    '정산차이',
]
