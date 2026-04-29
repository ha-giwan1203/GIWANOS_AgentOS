# D0 업로드 — 작업 스케줄러 등록 안내

> 본 폴더는 D0_SP3M3 Morning/Night 자동 실행 로그 저장소.
> Phase 7 사후 검증·자동 재실행 wrapper(`run_morning_recover.bat`)는 사용자가 Windows 작업 스케줄러로 직접 등록.

## 의제 합의
- 토론: `90_공통기준/토론모드/logs/debate_20260429_121732_3way/` (Round 1 pass_ratio 1.00, 양측 통과)
- 채택안 6대 단위: 원인 분류 4종 + 백오프 1/5/15/30분 + Phase 0/1/2 한정 강제 종료 + dedupe 매번 + lock os.O_EXCL + DOM 저장

## 신규 등록 작업 스케줄러

### 1. D0_SP3M3_Morning_Recover (07:30, morning 20분 후)
관리자 PowerShell:
```powershell
schtasks /create `
  /TN "D0_SP3M3_Morning_Recover" `
  /TR "C:\Users\User\Desktop\업무리스트\90_공통기준\스킬\d0-production-plan\run_morning_recover.bat" `
  /SC DAILY /ST 07:30 /F
```
또는 GUI 작업 스케줄러:
- 트리거: 매일 07:30
- 동작: `C:\Users\User\Desktop\업무리스트\90_공통기준\스킬\d0-production-plan\run_morning_recover.bat`
- 시작 위치: `C:\Users\User\Desktop\업무리스트\90_공통기준\스킬\d0-production-plan`
- 권한: 가장 높은 권한으로 실행

### 2. D0_SP3M3_Night_Recover (야간 작업 30분 후)
> Phase 1은 morning 우선. 야간 verify는 `verify_run.py --session night` 호환 (Phase 2 이월).

야간 wrapper(`run_night_recover.bat`)는 morning wrapper 복제 후 `--session night`로 변경하면 즉시 사용 가능. 야간 시간대는 사용자 야간 작업 스케줄러 시간 + 30분.

## 동작 요약
1. morning 07:10 실행 (기존 `D0_SP3M3_Morning`)
2. morning_<today>.log 작성
3. **07:30 verify 발화** (신규)
   - 로그 파일 존재 + 종료 마커 검증
   - 실패 시 원인 분류 → RETRY_OK 백오프(1/5/15/30분) / RETRY_BLOCK·RETRY_NO 즉시 알림
   - 매 재시도 전 dedupe 선행
   - 누적 51분 한계
4. 알림 stub: `.claude/state/d0_verify_notify.jsonl` (Phase 2 이월: Slack MCP 통합)

## 검증 (사용자 등록 후 1회)
```
cd C:\Users\User\Desktop\업무리스트\90_공통기준\스킬\d0-production-plan
python verify_run.py --session morning --line SP3M3 --dry-run
```
정상 동작 시 stdout에 분류·백오프·dedupe·종료 로그 출력 (재실행 안 함).

## 로그 파일
- `morning_<YYYYMMDD>.log` — 기존 morning 작업 결과
- `morning_<YYYYMMDD>_manual.log` — 수동 복구 로그
- `recover_<YYYYMMDD>_<HHMMSS>.log` — verify_run.py 실행 결과 (신규)

## 비상 롤백
재실행으로 잘못 등록된 건 발생 시:
```
python .claude/tmp/erp_d0_dedupe.py --line SP3M3 --date <today> --execute
```
SmartMES rank 작은 쪽 보존 / 큰 쪽 삭제 자동 정리.

## 참고
- 본 wrapper는 morning만. 야간은 동일 패턴 복제 (Phase 2 이월).
- Slack MCP 통합은 Phase 2 이월 (현재는 jsonl 기록).
- 1주 운영 후 hook_log·incident_ledger 누적 분석 → 분류기 정합성 보고.
