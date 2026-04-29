# HANDOFF — AI 인수인계 문서 (세션 메모 전용)

> **이 파일은 세션 인수인계 메모다. 상태 원본이 아니다.**
> 작업 완료/미완료 판정은 TASKS.md 기준. 이 파일이 TASKS와 충돌하면 TASKS를 따른다.
> 세션 변경사항과 다음 AI 액션만 기록한다. 완료/미완료를 독립 선언하지 않는다.

최종 업데이트: 2026-04-29 KST — 세션126 [C] jobsetup-auto 신규 스킬 v0.3 + d0-production-plan v3.1 야간 dedupe / 세션125 [3way] 알잘딱깔센 진단 + share_after_push hook + 메모리 4건 통합 / 세션124 [3way] GPT 재판정 통과 — 토론 close / 세션124 [3way] SP3M3 D0 OAuth 비login 정착 fallback / 세션124 [E] SP3M3 주간 D0 14건 등록 / 세션123 [C] write-router gate (sprawl 차단) / 세션122 [3way] Opus 체감 진단 + 빼는 안 4종
읽기 순서: **TASKS.md → STATUS.md → HANDOFF.md** → CLAUDE.md → 도메인 CLAUDE.md

---

## 세션126 (2026-04-29) — [C] SmartMES 잡셋업 자동화 + 야간 dedupe

### 진입
- 사용자: "샌산계획 반영후 후속작업 루틴 만들거야" → 후속작업 = "잡셋업 항목 입력 자동화"
- 트리거: 매일 아침 SP3M3 D0 morning 반영 완료 후 (하이브리드 = `/d0-plan` 끝부분 자동 호출)

### 결정 흐름 (사용자 답변)
1. **트리거 방식**: 하이브리드 (`/d0-plan` 끝부분 분기 신설)
2. **자동화 범위**: 측정값 = 허용오차 내 난수 / 이상유무 = OK 자동
3. **자동화 경로**: SmartMES UI computer-use (잡셋업 API 미공개)
4. **공정 범위**: 모든 공정 자동 순회
5. **저장 단위**: 첫 실행 관찰 후 확정 (Q2 "모름")
6. **작업자 인증**: 별도 (잡셋업 단독 처리 가능, [91] 진입 시 자동 매핑 확인)
7. **분포 정책 강화** (사용자 우려 반영): 균등 → 정규분포 (σ=오차/3, 시드 미고정)
8. **R5 롤백**: 재입력 + 재저장으로 정정 (별도 삭제 API 불필요)
9. **분기 시점 변경**: hand-off → 무인 자동 실행 (사용자 명시 승인)
10. **야간 dedupe**: 1~5행만 검사 + PROD_NO+수량 일치 시 제외

### 산출물 (신규 4 + 수정 4 = 8건)
- **신규**: `90_공통기준/스킬/jobsetup-auto/SKILL.md` (v0.3)
- **신규**: `90_공통기준/스킬/jobsetup-auto/state/screen_analysis_20260429.md` (선행 분석)
- **신규**: `.claude/commands/jobsetup-auto.md`
- **신규**: 메모리 `project_jobsetup_skill.md`
- **수정**: `.claude/commands/d0-plan.md` (Step 5 자동 호출)
- **수정**: `90_공통기준/스킬/d0-production-plan/run.py` (`dedupe_night_first_5` 함수)
- **수정**: `90_공통기준/스킬/d0-production-plan/SKILL.md` (Phase 4 step 16.5 + v3.1)
- **수정**: 메모리 `MEMORY.md` 인덱스 + plan `splendid-roaming-quilt.md`

### 선행 분석 결과 (제품 1.RSP3SC0383_A 기준)
- 11개 공정 + 17개 검사항목
- 측정값형(A) 6개 (A1 4건, A2 1건, A3 1건)
- OK/NG형(B) 11개
- 좌표 캘리브레이션 1456×819 모두 확정

### 다음 AI 액션
1. 오늘 저녁 17~19시 evening 세션 첫 실행 → `[dedupe]` 로그 검증 (수량 키 매칭 정상 동작)
2. 2026-04-30 07:05 morning D0 → 07:15+ 자동 `/jobsetup-auto --commit` 첫 실 가동
3. 첫 실행 결과로 저장 단위 확정 → SKILL.md Step 8 v1.0 승격
4. 매칭 키 미스매치 시 정확한 ERP 필드명으로 `dedupe_night_first_5` 재패치

---

## 세션125 (2026-04-29) — [3way] 알잘딱깔센 미달 진단 + 개선 방향 결정·구현

### 진입
- 사용자: "알잘딱깔센이 잘 안되는 근본적인 이유가 뭐니? 외부 자료를 찾아야 하나? 시스템의 한계인가?"
- Claude 1차 진단 (모드 B): drift 50% / instruction-bias 20% / hook 미구현 30%
- 사용자: "토론해서 개선 방향을 정하고 진행해바" → 3자 토론 진입

### 토론 합의 (Round 1 pass_ratio 1.00)
- 비중 재합의: hook 미구현이 본질 (40~70%)
- GPT 추가 후보: 목표 함수 오염 10% (drift 35%, bias 15%, hook 40%)
- Gemini: hook 미구현 70%+ (지시 종료 후 대기 상태 전환이 본질)
- 외부 자료: GPT는 Anthropic Claude Code 공식 hook 문서·LangGraph 체크포인트 인용 가치 / Gemini는 ReAct 패턴 인용 / 양측 모두 "추가 일반 조사는 불필요, 현재 이벤트 활용이 시급"

### 채택안 4건 (실행 완료)
- **Phase A**: memory 4건 통합 (no_approval_prompts / no_idle_report / post_completion_routine / auto_update_on_completion → feedback_post_push_share.md 단일 ECA "WHEN post-event THEN 자동 진행"). MEMORY.md 인덱스 11→8건. 기존 4건은 deprecated 표기 + 본문 보존
- **Phase B**: `.claude/hooks/share_after_push.sh` 신설 (23줄, advisory only, PostToolUse Bash + git push 패턴 + 직전 commit이 [3way]/docs(state)/feat/fix/refactor일 때 stderr 경고 + hook_log 기록, exit 0 강제, 자동 share-result 호출 금지). settings.json/README.md/protected_assets.yaml 동시 갱신. hook 35→36, smoke 11/11 PASS
- **Phase C**: 7일 ROI 검증 이월 (~2026-05-06). gate 전환 보류 (양측 합의 — 과잉)
- **이월 의제**: attention drift 정확 비중 클린 세션 vs 현행 실증 비교 (debate_20260428 [잔존]에 동일 항목)

### 자기 점검 (사용자 체감 짚음)
- 본 세션 share-result 자체도 사용자가 "공유 안하나?"라고 짚어야 시작 — 메모리 11건(추정) 누적인데 미발화. 토론 결론대로 Phase A+B로 보완. 다음 git push부터 hook이 stderr로 직접 경고

### 다음 AI 액션
1. Phase B hook 동작 1주 모니터링 (hook_log.jsonl 발화 횟수 + 후속 share-result 실행 비율)
2. 2026-05-06 1주 후 ROI 결과 보고
3. 잔존: 2026-04-30 07:05 morning auto-run LastResult=0 검증 (세션124 D0 OAuth 패치 실증, 시간 07:10→07:05 사용자 결정 변경)

### [완료] 즉시 처리 안건 1 — TASKS.md 1104→833줄 감축 (271줄)
- 98_아카이브/TASKS_archive_세션98-104_20260429.md로 분리 (로컬 전용 gitignored)
- TASKS.md 본문에서 세션98~104 항목 제거 + 안내 라인 1줄 추가
- 권장 감축 282줄에 부합 (271줄 = 96%)
- SessionStart STRONG 경고 해소 예정

### [완료] 즉시 처리 안건 2 — incident 분석 + debate_verify 1건 보강
- 미해결 incident 133건 (보고된 122건과 약간 차이) 분류:
  - 28건은 **정상 안전장치 발화**(completion_before_state_sync 14 / pre_commit_check 7 / evidence_missing 4 / harness_missing 4) — 시스템 정상 작동 증거. 토론 합의대로 hook으로 외부 비트 주입 효과로 해석
  - 9건 session_drift / 9건 debate_verify / 4건 기타 — 별도 분석 의제
- 본 세션125 토론(`debate_20260429_103117_3way`) result.json + step5_final_verification.md 작성 → debate_verify hook 미래 통과 보강 (1건 해소)
- 자동 일괄 수리는 안 함 (auto-fix는 분석+제안 전용, SKILL.md 규정)

### [완료] 안건 4 — D0 스케줄러 사후 검증 + 자동 재실행 (사용자 명시 모드 C)
- 의제: "스케줄러 실패 시 자동 재실행, 중복 스스로 체크, 원인 판단해서 성공할 때까지"
- 토론: `debate_20260429_121732_3way` Round 1 pass_ratio 1.00, 양측 통과
- 채택안 6대 단위 (Claude 1차안 vs 양측 보강):
  - UNKNOWN 2회 → 1회 (양측 반대로 폐기)
  - 즉시/5/15/30 → 1/5/15/30분 (Gemini 1분 유예 채택)
  - 원인 분류 5종 → 4종 + RETRY_BLOCK 신설 (GPT/Gemini 통합)
  - schtasks 강제 종료 → Phase 0/1/2 한정 (Phase 3+ 금지, 양측 합의)
  - lock 단순 → os.O_EXCL + PID·시각·stale 60분 (양측 합의)
  - DOM/스크린샷 저장 (Gemini 신규)
- 산출물: verify_run.py(290줄) + run_morning_recover.bat + SKILL.md Phase 7 + README schtasks 안내
- critic WARN: 4키 긍정 일색 + 보류→채택 경위 부족 (결론 영향 없음)
- **양측 부분PASS 후속 보강 commit (실증 결함 3건)**: classify_failure 모든 RETRY_OK Phase 3+ → RETRY_BLOCK / Phase unknown 강제 종료 차단 / SKILL DOM stub 정확화
- **사용자 작업 필요 (시간 사용자 결정 반영)**:
  - 기존 `D0_SP3M3_Morning` 시간 변경: `schtasks /change /TN "D0_SP3M3_Morning" /ST 07:05` (07:10 → 07:05)
  - 신규 `D0_SP3M3_Morning_Recover` 등록 (07:15, morning 10분 후): README에 명령 안내

### 다음 AI 액션 (재정리)
1. 사용자가 schtasks 등록 후 다음 morning(2026-04-30 07:05) 발화 + 07:15 recover 발화 검증
2. 1주 운영 후 hook_log·incident_ledger 누적 분석 → 분류기 정합성 보고
3. Phase 2 이월: Slack MCP 통합 / 야간 verify wrapper / 분류기 개선

---

## 세션124 (2026-04-29) — [E] SP3M3 주간 D0 14건 등록 + auto-run OAuth 실패 복구

### 진행 상황
- 진입: 사용자 "spm3주간계획 반영 되었는지 확인" → 로그 확인 → 미반영 발견 → 사용자 "진행" → E 모드 복구
- 모드: E (장애 복구 — OAuth 자동실행 실패 차단)

### 자동실행 실패 원인 (실증)
- `06_생산관리/D0_업로드/logs/morning_20260429.log`: 07:10 시작, 07:11 OAuth 완료 2회 실패로 종료
- URL 정착: `auth-dev.samsong.com:18100/login?error` → `auth-dev.samsong.com:18100/` (클라이언트 선택 화면, title="SAMSONG | OAuth", BOM/ERP/MES/SCM/PMS/DXMS 메뉴)
- run.py `ensure_erp_login`(:115)은 `auth-dev/login` URL에서만 작동 → 클라이언트 선택 화면 무인식 → `_wait_oauth_complete` 30s timeout
- `navigate_to_d0`(:154-160)는 첫 http 탭 우선 선택 → auth-dev 탭부터 잡음

### 복구 조치
- playwright CDP 9223 접속 → auth-dev 탭을 D0 URL(`/prdtPlanMng/viewListDoAddnPrdtPlanInstrMngNew.do`)로 직접 navigate
- 재실행: `python run.py --session morning --line SP3M3` → Phase 0~6 전 통과
- 결과: 14건 등록 / rank_batch 14/14 / mesMsg statusCode=200 / SmartMES 검증 ✅
- 코드 변경 0줄, 외부 상태(브라우저 탭 navigate) 1회만 — E 최소 패치 정량 충족

### 지침 준수 자가점검
- 초기 실수: SKILL.md 미독 상태에서 dry-run 2회 시도 + 탭 닫기 권한 거부 → 사용자 "스킬과 지침 확인 안하나?" 지적
- 정정: SKILL.md / d0-plan.md 독해 → 옵션 4안 정리 후 사용자에게 선택 위임
- 세션121 "SKILL.md 원본 미독 진행" 재발 — 같은 사고 패턴 1회 더

### 다음 AI 액션
1. **사후 B 분석**: 3자 토론에서 (d) 단독 채택으로 종결됨 — 후보 (a)/(b)/(c) 보류·버림
   - (a) `_wait_oauth_complete` 클라이언트 선택 화면 감지 + ERP 자동 클릭 → 보류 (DOM 의존성 불안정)
   - (b) `navigate_to_d0` auth-dev 탭 자동 스킵 → 버림 ((d) 만으로 동일 효과)
   - (c) (a)+(b) 결합 → 버림 (최소성 원칙)
2. **잔존 실증 검증** (시간 도래 후 별도 세션): 2026-04-30 07:10 morning auto-run LastResult=0 + morning_20260430.log 정상 종료 + exit code 0

### 추가 (3자 토론 + 근본 패치)
- Round 1 합의 (debate_20260429_075455_3way, pass_ratio 1.00): (d) `_wait_oauth_complete` 30s 실패 + 비login auth-dev URL일 때 `_safe_goto(D0_URL)` 1회 시도 + 재대기 — 5줄 elif 추가 (commit b4ab2fea)
- commit_gate.sh 근본 패치: circuit breaker `echo` stdout/stderr 출력 제거 (Claude Code PreToolUse hook 프로토콜이 출력을 block 응답으로 오인하는 false-block 해소). hook_log 기록은 유지 (commit 0c81d1fb)
- 양측 최종 검증: Gemini 통과 / GPT 통과 (재판정 완료 — round1_final.md L5)

---

> **이전 세션 이력 아카이브**: `98_아카이브/handoff_archive_20260427_20260428.md`
