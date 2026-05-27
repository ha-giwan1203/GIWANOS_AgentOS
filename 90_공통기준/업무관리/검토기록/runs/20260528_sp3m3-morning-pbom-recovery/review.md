# SP3M3 주간계획 P-BOM 미등록 복구 (2026-05-28 morning)

## 결과
- SmartMES SP3M3 2026-05-28 R 상태 15건 박힘 (rank 1~15)
- 보류 2건: RSP3SC0245, RSP3SC0246 — P-BOM 마스터 미등록 → 현업 등록 후 별도 추가

## 사고 시퀀스
1. 07:10 cron 자동 실행 → Phase 3 (ERP D0 17건 등록 REG_NO 334797~334813) + Phase 4 (서열 17건) 완료
2. Phase 5 final_save 호출 → `mesMsg: 제품 P-BOM 등록 안됨. [SP3M3, RSP3SC0246] statusCode=850` → 17건 일괄 MES 거부
3. verify_run.py → `phase6_verify_failed / RETRY_NO 자동 재실행 중단` → 알림 없이 종료
4. 07:49 사용자 발화 "sp3m3 주간계획 반영" → 재시도해도 dedupe로 0건 (ERP totGrid에는 17건 등록 상태)
5. 사용자 명시 동의 → Phase 5 final_save 단독 재호출, RSP3SC0245/0246 누적 제외 → MES 200 PASS, SmartMES 15건

## 변경 파일
- `90_공통기준/스킬/d0-production-plan/run.py` — `--exclude PROD_NO,...` 옵션 추가 (phase1 직후 items 제외, E 모드 복구용)

## 발견된 구조적 약점
1. **P-BOM 미등록 사전 가드 부재** — 마지막 단계 MES에서만 검증. 추출 단계에서 자동 분리 불가.
2. **ERP/MES 1건씩 보고** — 1회 호출당 첫 P-BOM 미등록 1건만. N건 미등록 시 N회 호출 필요.
3. **cron fail 알림 채널 부재** — verify가 stderr만 출력. 사용자 라인 가동 직전까지 인지 불가.

## 후속 (별도 작업)
- P-BOM 사전 조회 가드 (xlsm 추출 직후 미등록 품번 자동 분리)
- cron fail 텔레그램 알림
- P-BOM 미등록 자동 누적 제외 루프 정식화 (오늘 `.claude/tmp/final_save_loop_20260528.py` → SKILL run.py 옵션화)

## 임시 산출물 (push 제외 — `.claude/tmp/`)
- `delete_reg_20260528.py` — ERP D0 DELETE (334797/334798 2건 성공, 나머지 500 동시성 fail)
- `final_save_only_20260528.py` — Phase 5 단독 재호출 1차
- `final_save_loop_20260528.py` — P-BOM 미등록 자동 누적 제외 루프 (이번 복구에 사용)
- `grid_readonly.py` — totGrid 조회
- `smartmes_check_20260528.py` — SmartMES R 상태 조회
