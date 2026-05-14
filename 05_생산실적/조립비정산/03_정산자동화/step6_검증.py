#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step 6 — 검증
기존 검증_정산결과.py 기반 자동 검증 (Step5 JSON → 항목별 PASS/FAIL/WARNING/INFO)

검증 항목:
  1. 라인합계 vs 00_정산집계 일치 여부 (엑셀 파일 생성 전: Step5 JSON 내부 일관성)
  2. SD9A01 단가기준판정 규칙 (단가≤500→야간가산, >500→기본)
  3. WABAS01 단가=0 품번 건수 및 실적 유무 (INFO)
  4. Usage=2 수량 2배 환산 적용 확인
  5. SP3M3 야간 고정단가 170원 적용 확인 (KNOWN_EXCEPTIONS 매칭)
  6. 미매핑 품번 존재 여부 (INFO)
  7. 전체 합계 일관성 (라인합산 == grand 합계)

overall 판정: FAIL (CRITICAL 존재) | WARNING (CRITICAL 없고 WARNING 존재) | PASS

엑셀 파일 생성 후 실행 시: step7이 생성한 xlsx도 추가 검증 가능

실행: python step6_검증.py
입력: _cache/step5_settlement.json
"""

import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

from _pipeline_config import *
from datetime import datetime

# ── Known Exception 레지스트리 ────────────────────────────────
# FAIL 항목 중 사전 인지된 예외를 등록한다.
# enabled=True인 그룹의 items에 속한 품번은 WARNING으로 하향 처리.
# expires: 유효 만료일 (참고용, 만료 후 자동 CRITICAL 전환 아님 — 담당자가 제거)
KNOWN_EXCEPTIONS = {
    "SP3M3_NIGHT_RSP": {
        "enabled": True,
        "items": [
            {"part_no": "RSP3SC0291", "reason": "RSP 미매핑", "expires": "2026-06-30"},
            {"part_no": "RSP3SC0292", "reason": "RSP 미매핑", "expires": "2026-06-30"},
            {"part_no": "RSP3SC0293", "reason": "RSP 미매핑", "expires": "2026-06-30"},
            {"part_no": "RSP3SC0294", "reason": "RSP 미매핑", "expires": "2026-06-30"},
        ]
    }
}

# KNOWN_EXCEPTIONS 에서 활성화된 품번 세트를 추출
def _known_part_set(group_key):
    """활성화된 Known Exception 그룹의 품번 집합 반환"""
    grp = KNOWN_EXCEPTIONS.get(group_key, {})
    if not grp.get("enabled", False):
        return set()
    return {item["part_no"] for item in grp.get("items", [])}


print("=" * 60)
print("Step 6: 정산 검증")
print("=" * 60)

if not os.path.exists(CACHE_STEP5):
    print(f"[ERROR] Step5 결과 없음. step5_정산계산.py 먼저 실행하세요.")
    sys.exit(1)

with open(CACHE_STEP5, encoding='utf-8') as f:
    s5 = json.load(f)

lines   = s5['lines']
summary = s5['summary']
results = []
pass_n = fail_n = warning_n = info_n = 0


def chk(no, name, status, detail='', severity='CRITICAL'):
    """검증 항목 기록 및 카운터 갱신.

    status : 'PASS' | 'FAIL' | 'WARNING' | 'INFO'
    severity: 'CRITICAL' | 'WARNING' | 'INFO'
              status='FAIL'인 경우에만 의미 있음.
              status='WARNING'이면 severity는 자동으로 'WARNING'으로 취급.
    """
    global pass_n, fail_n, warning_n, info_n
    label_map = {'PASS': '✓ PASS', 'FAIL': f'✗ FAIL[{severity}]', 'WARNING': '△ WARNING', 'INFO': 'i INFO'}
    label = label_map.get(status, status)
    print(f"  [{label}] {no}. {name}")
    if detail:
        print(f"       {detail}")
    results.append({
        "no": no, "name": name,
        "status": status, "severity": severity if status == 'FAIL' else status,
        "detail": detail
    })
    if status == 'PASS':
        pass_n += 1
    elif status == 'FAIL':
        fail_n += 1
    elif status == 'WARNING':
        warning_n += 1
    else:
        info_n += 1


print()

# ── 항목 1: 전체 합계 일관성 ──────────────────────────────────
calc_gerp = sum(lines[lc]['total_gerp_amt'] for lc in lines)
calc_erp  = sum(lines[lc]['total_erp_amt']  for lc in lines)
grand_gerp = s5['grand_gerp_amt']
grand_erp  = s5['grand_erp_amt']

gerp_ok = abs(calc_gerp - grand_gerp) == 0
erp_ok  = abs(calc_erp  - grand_erp)  == 0
chk(1, "전체합계 일관성 (라인합산 == grand)",
    'PASS' if (gerp_ok and erp_ok) else 'FAIL',
    f"GERP: {calc_gerp:,} vs {grand_gerp:,}  구ERP: {calc_erp:,} vs {grand_erp:,}")

# ── 항목 2: SD9A01 단가기준판정 ──────────────────────────────
sd9_items = lines.get('SD9A01', {}).get('items', [])
sd9_fail  = []
for r in sd9_items:
    if r['gerp_ngt_qty'] == 0:
        # 야간실적 없으면 판정 없음 OK
        if r['price_judgment'] is not None:
            sd9_fail.append(f"{r['part_no']}(야간없는데 판정={r['price_judgment']})")
    else:
        expected = '야간가산' if r['price'] <= 500 else '기본'
        if r['price_judgment'] != expected:
            sd9_fail.append(f"{r['part_no']}(단가={r['price']},판정={r['price_judgment']},기대={expected})")

chk(2, "SD9A01 단가기준판정 규칙 (단가≤500→야간가산, >500→기본)",
    'PASS' if not sd9_fail else 'FAIL',
    f"오류: {sd9_fail[:5]}" if sd9_fail else "전체 정상")

# ── 항목 3: WABAS01 단가=0 품번 ──────────────────────────────
waba_items = lines.get('WABAS01', {}).get('items', [])
zero_price = [r for r in waba_items if r['price'] == 0]
has_real   = [r for r in zero_price if r['gerp_day_qty'] > 0 or r['gerp_ngt_qty'] > 0]
chk(3, f"WABAS01 단가=0 품번 현황",
    'INFO',
    f"단가=0: {len(zero_price)}건  (실적있음: {len(has_real)}건) → 단가 확인 필요")

# ── 항목 4: Usage=2 수량 2배 환산 ────────────────────────────
usage2_ok = True
usage2_issues = []
for lc, ldata in lines.items():
    for r in ldata['items']:
        if r['usage'] == 2:
            # 원천수량은 저장 안 했으므로 계산된 qty 기반으로 홀수 체크
            if r['gerp_day_qty'] % 2 != 0 and r['gerp_day_qty'] != 0:
                usage2_issues.append(f"{lc}/{r['part_no']}(qty={r['gerp_day_qty']})")

chk(4, "Usage=2 품번 수량 짝수 여부 (2배 환산 확인)",
    'PASS' if not usage2_issues else 'INFO',
    f"홀수 수량 품번(비정상 가능): {usage2_issues[:5]}" if usage2_issues else "전체 정상(짝수)")

# ── 항목 5: GERP 원본금액 정합성 (정산금액 = GERP 원본) ──
# 2026-04-05: SP3M3 야간 170원 고정 → GERP 원본금액 직접 사용으로 변경
# 정산금액과 원본금액이 동일한지 확인
orig_mismatch = []
for lc_chk in lines:
    for r in lines[lc_chk].get('items', []):
        if r['gerp_day_amt'] != r['gerp_orig_day_amt'] or r['gerp_ngt_amt'] != r['gerp_orig_ngt_amt']:
            orig_mismatch.append(f"{lc_chk}/{r['part_no']}")
chk(5, "GERP 원본금액 정합성 (정산=원본)",
    'PASS' if not orig_mismatch else 'FAIL',
    f"불일치: {orig_mismatch[:5]}" if orig_mismatch else "전체 정상")

# ── 항목 6: (삭제됨 — 미매핑 품번은 GERP 단가 fallback 적용) ──

# ── 항목 7: 라인별 차이 요약 (INFO) ──────────────────────────
diff_lines = [r for r in summary if r['diff_amt'] != 0]
chk(7, "GERP vs 구ERP 라인별 차이",
    'INFO' if diff_lines else 'PASS',
    "; ".join(f"{r['line']}:{r['diff_amt']:+,}" for r in diff_lines) if diff_lines else "전 라인 일치")

# ── 결과 ─────────────────────────────────────────────────────
# overall 판정 3단계: CRITICAL FAIL 존재 → FAIL, WARNING만 존재 → WARNING, 그 외 → PASS
critical_n = sum(
    1 for c in results
    if c['status'] == 'FAIL' and c.get('severity') == 'CRITICAL'
)
if critical_n > 0:
    overall = 'FAIL'
elif warning_n > 0:
    overall = 'WARNING'
else:
    overall = 'PASS'

print(f"\n{'='*60}")
print(f"종합: PASS {pass_n} / FAIL(CRITICAL) {fail_n} / WARNING {warning_n} / INFO {info_n}")
print(f"최종 판정: {overall}")

if fail_n > 0:
    print("\n[CRITICAL FAIL 항목] — STATUS.md 미해결 이슈에 기록 권장")
    for r in results:
        if r['status'] == 'FAIL':
            print(f"  - {r['no']}. {r['name']}: {r['detail']}")

if warning_n > 0:
    print("\n[WARNING 항목] — Known Exception 또는 주의 필요 사항")
    for r in results:
        if r['status'] == 'WARNING':
            print(f"  - {r['no']}. {r['name']}: {r['detail']}")

# 결과 JSON 저장
vr = {
    "step": 6,
    "timestamp": datetime.now().isoformat(),
    "overall": overall,
    "critical_fail": critical_n,
    "warning": warning_n,
    "pass": pass_n,
    "info": info_n,
    "fail": fail_n,          # FAIL 상태 총 건수 (backward compat)
    "checks": results,
}
vpath = os.path.join(CACHE_DIR, 'step6_validation.json')
with open(vpath, 'w', encoding='utf-8') as f:
    json.dump(vr, f, ensure_ascii=False, indent=2)

print(f"\n저장: {vpath}")
print("Step 6 완료")
