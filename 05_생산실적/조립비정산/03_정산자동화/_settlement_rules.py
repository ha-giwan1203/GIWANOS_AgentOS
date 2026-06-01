#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""정산 권위 룰 사전 (Single Source of Truth)

매월 정산에서 반복 발견되는 룰 위반의 근본 원인 = 도메인 룰이 텍스트 문서엔
박혀 있는데 빌더 코드와 동기화 안 됨. 이 모듈을 권위로 삼아 step2 / step5 /
step7 / step8 / build_formula_version / monthly-pnl-rollup 공통 참조.

룰 변경 시 이 파일만 수정. 텍스트 문서(CLAUDE.md / STATUS.md / 도메인.md)는
참조용 설명만. 코드 권위는 이 사전.

작성: 2026-06-01 (5월 정산 5건 룰 위반 사고 회고)
"""

# ──────────────────────────────────────────────────────────────
# 1. 라인 그룹 (10개 라인 3그룹)
# ──────────────────────────────────────────────────────────────
COMPLETION_LINES   = frozenset({'SD9A01', 'ANAAS04', 'DRAAS11'})
MAIN_SUB_LINES     = frozenset({'SP3M3', 'HASMS02', 'HCAMS02', 'ISAMS03'})
WEBBING_SUB_LINES  = frozenset({'WAMAS01', 'WABAS01', 'WASAS01'})
ALL_LINES          = COMPLETION_LINES | MAIN_SUB_LINES | WEBBING_SUB_LINES

LINE_GROUP = {
    **{l: '완성품'   for l in COMPLETION_LINES},
    **{l: '메인SUB' for l in MAIN_SUB_LINES},
    **{l: '웨빙SUB' for l in WEBBING_SUB_LINES},
}


# ──────────────────────────────────────────────────────────────
# 2. 이관 (정산 제외) 룰
# ──────────────────────────────────────────────────────────────
# 사용자 룰 정정 이력:
#   2026-05-07: SVM/OVK 라인 한정 + 88820X 차종 무관 (잘못 박힘)
#   2026-06-01: 88820X도 완성품 라인 한정 (사용자 룰 회복, SUB 부당 제외 사고 후)
SVM_TRANSFER_LINES    = MAIN_SUB_LINES      # SVM 차종 + 메인SUB 라인 = 이관
OVK_TRANSFER_LINES    = COMPLETION_LINES    # OVK 차종 + 완성품 라인 = 이관
X88820_TRANSFER_LINES = COMPLETION_LINES    # 88820X 시작 + 완성품 라인 = 이관

# OVK 라인 + 89880X 시작 품번은 이관 아님 (사용자 룰 2026-05-07)
OVK_EXCLUDE_PREFIX = '89880X'


def is_transferred(line: str, vtype: str, product_no: str):
    """GERP raw 행이 정산 이관 대상인지 판정.

    Returns:
        (category, reason) — 이관이면 ('SVM'/'OVK'/'88820X', 설명), 아니면 (None, None)
    """
    line = str(line or '').strip()
    vtype = str(vtype or '').strip()
    pn = str(product_no or '').strip()

    if line in SVM_TRANSFER_LINES and vtype == 'SVM':
        return ('SVM', '이관품번(SVM·메인SUB)')
    if line in OVK_TRANSFER_LINES and vtype == 'OVK' and not pn.startswith(OVK_EXCLUDE_PREFIX):
        return ('OVK', '이관품번(OVK·완성품)')
    if pn.startswith('88820X') and line in X88820_TRANSFER_LINES:
        return ('88820X', '이관품번(88820X·완성품)')
    return (None, None)


# ──────────────────────────────────────────────────────────────
# 3. 비용 항목 부호 룰 (라인정지·재작업·기타생산비용)
# ──────────────────────────────────────────────────────────────
# 도메인 룰 (사용자 명시 2026-06-01):
#   라인정지·재작업·기타생산비용은 G-ERP 라인보상 / QIS Claim 시스템에서 청구.
#   귀책 = 사내부서(생산기술팀·품질관리팀 등) 또는 납품업체(선일다이파스·웰텍스 등)
#     → 그들이 우리(대원테크)에게 보상 → C 비용보전 (+, 가산)
#   귀책 = 대원테크
#     → 우리가 줘야 할 돈 → D 차감비용 (-, 차감)
COST_BLAME_CATEGORIES = {
    'INTERNAL':  {'생산기술팀', '품질관리팀', '생산관리팀', '연구개발팀'},  # 사내부서
    'SUPPLIER':  set(),  # 납품업체 (이름 다양 — 패턴 매칭으로 처리)
    'OURSELVES': {'대원테크', '대원'},  # 우리 귀책
}


def cost_sign(blame: str) -> str:
    """비용 항목 부호 판정. 귀책에 따라 'C'(가산) / 'D'(차감) 반환."""
    blame = str(blame or '').strip()
    if blame in COST_BLAME_CATEGORIES['OURSELVES']:
        return 'D'  # 우리가 줘야 함
    return 'C'  # 사내부서·납품업체·공란 default = 받을 금액


# ──────────────────────────────────────────────────────────────
# 4. 외부 지원 파일 부호 룰 (화인텍 등)
# ──────────────────────────────────────────────────────────────
# 매월 방향 다름. 우선순위:
#   1) 파일 안 `_meta` 시트 / A1 셀에 박힌 부호 (+1/-1) 직접 읽기
#   2) 파일명·시트명 토큰 매칭
#   3) 매칭 없으면 skip + 사용자 통보
SUPPORT_NEG_TOKENS = ['지원받은', '받은']           # -1 (우리가 받음 → 회사 입장 지출)
SUPPORT_POS_TOKENS = ['지원해줌', '지원함', '→']    # +1 (우리가 줌  → 회사 입장 수입 청구)


def detect_support_sign(filename: str, sheetname: str, title: str = '', meta_sign=None) -> int:
    """지원 파일 부호 판정. 0 = 명확 안 됨 (skip)."""
    if meta_sign in (-1, 1):
        return meta_sign  # 사용자 명시 cell 우선
    text = f"{filename} {sheetname} {title}"
    for tok in SUPPORT_NEG_TOKENS:
        if tok in text:
            return -1
    for tok in SUPPORT_POS_TOKENS:
        if tok in text:
            return +1
    return 0


# ──────────────────────────────────────────────────────────────
# 5. SP3M3 BI 보정 룰 (E 산정)
# ──────────────────────────────────────────────────────────────
# 산식: E = max(0, BI 야간 EA - GERP raw 야간 EA) × 170원
# GERP raw 야간 = "추가" 행 qty 합 (정산집계 dedupe 후 값 사용 금지 — 권위는 raw)
SP3M3_BI_UNIT_PRICE = 170
SP3M3_BI_LINE = 'SP3M3'


# ──────────────────────────────────────────────────────────────
# 6. 야간 정산 룰 (2026-05-08 통합)
# ──────────────────────────────────────────────────────────────
# 야간 정산금액 = GERP raw "추가" 행 그대로 (이미 단가 × 0.3 적용된 단가가 raw에 입력됨)
# 빌더 추가 가산(× 1.3 등) 적용 금지 — 전 라인 동일 룰
NIGHT_SHIFT_VALUE = '추가'
DAY_SHIFT_VALUE   = '정상'


# ──────────────────────────────────────────────────────────────
# 7. 이관품번 오류리스트 분류 패턴 (X2)
# ──────────────────────────────────────────────────────────────
# 오류리스트 X2 분류 (제외사유 = '이관품번') 자동 박는 패턴
TRANSFER_PN_PATTERNS = ['X9000', 'X9500', 'X9230']
TRANSFER_PN_PREFIXES = ['88820X', 'MO89870X', 'MO89880X']


# ──────────────────────────────────────────────────────────────
# 8. 웨빙 재작업 품번 (X3 분류)
# ──────────────────────────────────────────────────────────────
WEBBING_REWORK_PARTS = frozenset({'89830R1200NNB'})


# ──────────────────────────────────────────────────────────────
# 9. 다중단가 정합 룰 (X1 분류)
# ──────────────────────────────────────────────────────────────
# 동일품번 다중단가 → 빌더는 첫 행에만 구ERP 합산 → 정합 인정(다중단가분배)
# 제외사유 = '정합인정(다중단가분배)'


# ──────────────────────────────────────────────────────────────
# 10. 업체 코드
# ──────────────────────────────────────────────────────────────
VENDOR_CODE = '0109'  # 대원테크


# ──────────────────────────────────────────────────────────────
# 룰 사전 사용 위치 매핑 (단계적 통합 추적)
# ──────────────────────────────────────────────────────────────
# 통합 완료:
#   - (없음, 본 모듈 신설 직후)
#
# 통합 예정 (TASKS 9차~):
#   - step2_GERP처리.py L60~75: SVM_TRANSFER_LINES / OVK_TRANSFER_LINES / X88820_TRANSFER_LINES
#   - build_formula_version.py: is_transferred() 호출
#   - _error_types.py L54~56: TRANSFER_PN_PATTERNS / TRANSFER_PN_PREFIXES
#   - monthly-pnl-rollup/run.py compute_pnl: cost_sign() / detect_support_sign()
#   - monthly-pnl-rollup/builders/sheet_94_support.py: SUPPORT_NEG/POS_TOKENS
#   - monthly-pnl-rollup/run.py extract_bi_night_total: SP3M3_BI_UNIT_PRICE / SP3M3_BI_LINE
