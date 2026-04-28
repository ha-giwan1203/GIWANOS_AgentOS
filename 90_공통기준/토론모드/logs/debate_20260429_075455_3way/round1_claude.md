# Round 1 — Claude 독자 답안 (Step 6-0)

세션124 사후 패치. 양측 본론 수령 전 작성.

## 의제
SP3M3 morning auto-run OAuth 클라이언트 선택 화면(`auth-dev.samsong.com:18100/`, BOM/ERP/MES/SCM/PMS/DXMS) 정착 시나리오 재발 방지 패치 결정.

## 결론 1줄
**(d) `_wait_oauth_complete` 30s 실패 + 비login URL일 때 `raise` 대신 `_safe_goto(D0_URL)` 1회 시도 + 재대기 (~3줄)** 채택.

## 주장 (라벨 + 증거)

1. **(d)는 오늘 수동 복구가 그대로 한 동작이다 — 실증됨**
   - 증거: `06_생산관리/D0_업로드/logs/morning_20260429_manual.log` (14/14 OK), 수동 조치 = playwright `target.goto(D0_URL)`
   - run.py:192~ `_safe_goto`는 동일 로직(page.goto + JS fallback) 이미 보유

2. **(a) DOM 매칭 의존은 SAMSONG OAuth 화면 변경 시 깨짐 — 과잉설계**
   - 증거: ERP-DEV 화면은 외부 시스템. DOM 셀렉터·텍스트 매칭은 우리가 통제 못함
   - (a)에서 ERP 텍스트 클릭 fallback이 깨지면 다음 morning auto-run 침묵 실패 가능

3. **(b) 단독은 자동실행 첫 시점에 무효 — 환경미스매치**
   - 증거: 오늘 07:10 시점 첫 페이지는 auth-dev뿐. erp-dev 탭은 내가 수동으로 ERP 클릭 후 생성. (b)는 erp-dev 탭이 이미 있을 때만 의미

4. **(d)는 신규 함수·hook·gate·settings 추가 0 — E 정량 적합**
   - 증거: 기존 `_safe_goto` 재사용. C 모드 R1~R5 적용 시에도 변경량 ≤20줄 ≤2파일 충족

5. **R5 롤백 영향 0 — 코드 patch 외 외부 잔존 없음**
   - 증거: 변경 위치는 Phase 0(D0 진입 전). ERP/MES 등록 단계 미도달 → 잔존 데이터 발생 불가
   - 롤백: `git revert <SHA>` 1줄

## 반대 안 예상 약점

- **(d) 약점**: 클라이언트 선택 화면에서 D0_URL goto가 redirect 안 되는 예외 — 권한 부족·타 클라이언트 강제 선택·첫 등록 후 약관 동의 화면 등. 이때 `_safe_goto` 자체는 통과 후 `_wait_oauth_complete` 재대기에서 다시 실패 → 명확한 에러 메시지. 하지만 self-recovery 불가 → 사용자 수동 개입 필요
- 보강안: (d) + (b) — auth-dev 탭이 새로 생기는 시나리오 보호. 변경 ~5줄
- 보강안 채택 여부는 GPT/Gemini 의견 대조 후 결정

## 착수·완료·검증 조건

- 착수 조건: 모드 C plan-first + R1~R5 작성, 사용자 명시 승인
- 완료 조건: run.py `_wait_oauth_complete` 분기 ≤3줄 patch, dry-run 통과, commit on main
- 검증 조건: 다음 morning auto-run(2026-04-30 07:10) `D0_SP3M3_Morning` LastResult=0 + `morning_20260430.log` 정상 종료

## claude_delta 기준
- 본 답안 = 6-0 baseline. 6-5 종합안에서 변경량 측정.
