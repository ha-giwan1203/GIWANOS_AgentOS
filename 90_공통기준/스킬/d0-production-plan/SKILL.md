---
name: d0-production-plan
description: ERP D0 추가생산지시 자동화 (SP3M3 MAIN + SD9A01 OUTER). xlsm 추출 → ERP 업로드 → 서열 → MES 전송 → SmartMES 검증
trigger: "생산계획 반영", "D0 반영", "야간 계획 반영", "주간 계획 반영", "SP3M3 주간/야간/계획", "OUTER 계획", "SD9A01 계획", "생산지시 반영"
grade: B
---

# ERP D0 자동화 (SP3M3 / SD9A01)

> Phase 0~7 절차 / 모드 분기 / 핵심 주의사항 / 변경 이력은 [MANUAL.md](MANUAL.md). 용어는 ../GLOSSARY.json.
> 도메인 규칙: `90_공통기준/erp-mes-recovery-protocol.md`

⛔ **금지**: 엑셀 직접 열기 / 모니터 전환 / ERPSet Client(javaw.exe) 조작 / computer-use·마우스·키보드. 반드시 run.py 사용.
⛔ **사용자 첨부 가드**: xlsx/xlsm 첨부 발견 시 자동 실행 차단 — `--xlsx <path>` vs Z드라이브 자동 탐색 명시 확인 (2026-04-27 사고 재발 방지).

## 운영 세션 (하루 2회)
| 세션 | 시점 | 처리 |
|------|------|------|
| 저녁 17~19시 | SP3M3 야간 + SD9A01 OUTER D+1 |
| 아침 07:10 | SP3M3 주간 (3600 컷) |

## 사용
```bash
python run.py --session morning              # 아침 (하이브리드, default)
python run.py --session evening              # 저녁
python run.py --session auto                 # 시간대 자동
python run.py --session morning --legacy-mode    # 회귀 fallback
python run.py --session evening --dry-run        # 추출 검증
python run.py --session morning --xlsx <1건xlsx> --target-date YYYY-MM-DD   # 1건 PoC
python run.py --session morning --no-mes-send    # Phase 5 차단
```

## 절차 (요약)
1. Phase 0: CDP 9223 + ERP OAuth + D0 화면 진입
2. Phase 1: xlsm 탐색 (수정본 우선) + 시트 추출
3. Phase 1.5: dedupe (이미 등록 건 제외)
4. Phase 2: 업로드 xlsx 생성 (**Excel COM 필수**, openpyxl 금지)
5. Phase 3: selectListPmD0AddnUpload + multiListPmD0AddnUpload
6. Phase 4: 서열 배치 (하이브리드 default = requests 직접 POST, sendMesFlag='N')
7. Phase 5: 최종 저장 (sendMesFlag='Y' MES 전송)
8. Phase 6: SmartMES `/v2/prdt/schdl/list.api` 대조

## verify (Phase 7 사후 검증)
```bash
python verify_run.py --session morning --line SP3M3
# RETRY_OK(Phase 0~2) → 1/5/15/30분 백오프 (누적 51분 한계)
# RETRY_BLOCK(Phase 3+) → 즉시 종결
# RETRY_NO(파일/권한/마스터) → 알림
```

## 실패 시
- CDP/OAuth/Z드라이브/xlsm 미존재 / 서버 500 / MES != 200 → FAIL
- 되돌리기: `.claude/tmp/erp_d0_dedupe.py --line SP3M3 --date YYYYMMDD --execute` (SmartMES rank 자동 식별 + 안전 삭제)
- 상세 → MANUAL.md "핵심 주의사항" + "되돌리기"
