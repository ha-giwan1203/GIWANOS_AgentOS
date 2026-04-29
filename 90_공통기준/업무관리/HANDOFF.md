# HANDOFF — AI 인수인계 문서 (세션 메모 전용)

> **이 파일은 세션 인수인계 메모다. 상태 원본이 아니다.**
> 작업 완료/미완료 판정은 TASKS.md 기준. 이 파일이 TASKS와 충돌하면 TASKS를 따른다.
> 세션 변경사항과 다음 AI 액션만 기록한다. 완료/미완료를 독립 선언하지 않는다.

최종 업데이트: 2026-04-29 KST — 세션129 [측정] 정량 신호 3개 측정 시작 (옵션C, 1주/7세션) / 세션128 [C] block_dangerous false positive + config awk 파싱 버그 패치 / 세션128 [3way+A] 성능 실망 진단 + 옵션A 위생 정리 / 세션128 [E+C] ZDM DB 다운 → MES 단독 진행 + mes_login XSRF 패치 / 세션125 [3way] 알잘딱깔센 진단 + share_after_push hook + 메모리 4건 통합 / 세션124 [3way] GPT 재판정 통과 / 세션123 [C] write-router gate / 세션122 [3way] Opus 체감 진단
읽기 순서: **TASKS.md → STATUS.md → HANDOFF.md** → CLAUDE.md → 도메인 CLAUDE.md

---

## 세션129 (2026-04-29) — [측정] 정량 신호 3개 측정 시작 (옵션C)

### 진입
- 사용자: "이전세션 이어서 진행하자" → 세션128 잔존 항목 중 **정량 신호 측정 시작** 선택
- plan-first: `C:/Users/User/.claude/plans/virtual-bouncing-crab.md` 작성 + 사용자 승인

### 처리
- 측정 로그 신설: `90_공통기준/토론모드/logs/quant_signal_log.md`
- 신호 정의 + 1주(2026-05-06)·7세션 종료 조건 + 결정 규칙 명시
- 본 세션129 자기 측정 1행 기록: S1 60% / S2 PASS / S3 1건 → 부분 PASS
- 신규 hook/skill/command 0개 (S3 위반 회피 설계)

### 양측 PASS 확정 (3way 강제)
- GPT: PASS / item 1·2·3 모두 실증됨·동의 / 추가제안 A분류 1건 (S1 근거 보강)
- Gemini: PASS / item 1·2·3 모두 실증됨·동의 / GPT 판정 교차검증 동의 / 추가제안 A분류 1건 (S1 N/M 정량화)
- A분류 즉시 반영: quant_signal_log.md S1 측정 가이드에 "N줄 중 M줄" 정량 근거 의무 추가 + 본 세션 1행 (3/5) 기록

### 다음 AI 액션
- 다음 일반 세션 종료 시 quant_signal_log.md 1행 추가 (S1/S2/S3 정직 기록 + N/M 정량 근거)
- 7세션 누적 또는 2026-05-06 도달 시 결정 분기:
  - ALL ≥ 5/7 → 옵션B(구조 다이어트) 보류
  - ALL ≤ 2/7 → 옵션B 즉시 활성

---

## 세션128 (2026-04-29) — [C] block_dangerous false positive + config awk 파싱 버그 패치

### 처리
- block_dangerous.sh 2b 블록: `$COMMAND` 전체 grep → REDIRECT_TARGETS 토큰만 검사로 교체 (heredoc 본문 false positive 해소)
- hook_config.json danger_commands: `cat >`, `cat >>` 제거 (redirect는 2b가 처리)
- block_dangerous + protect_files config 파싱: awk → python3 안전 파싱 (한 줄 JSON 배열 인식 실패 버그 동시 수정)
- 검증 14/14 PASS, 회귀 영향 0

### 양측 PASS 확정 (3way 강제)
- GPT: PASS / item 3건 모두 실증됨·동의 / 추가제안 없음
- Gemini: PASS / item 3건 모두 실증됨·동의 / GPT 교차검증 동의 / 추가제안 없음
- share-result 정상 동작 — 본문에 보호 파일명 인용 있어도 차단되지 않음 (실측)

### 다음 AI 액션
- 다른 hook의 awk JSON 파싱 패턴 점검 (현재 block_dangerous + protect_files 외 0건 확인됨)
- 의제 종료. 다음 세션은 정량 신호 3개 측정 (옵션C 측정 세션 후보)

---

## 세션128 (2026-04-29) — [E+C] ZDM DB 다운 + MES 단독 + mes_login() XSRF 패치

### 진입
- 자동 trigger: scheduled-task `daily-routine`
- 1차 실행: ZDM `/api/daily-inspection` HTTP 500 → daily-routine 통합 스크립트 중단
- 2차 실행: 포트 자체 Connection Refused (서버 추가 악화)
- 3차 실행: HTTP 500 복귀 + 응답 본문 `{"success":false,"error":"Connection terminated due to connection timeout"}`
- 사용자 지적 "브라우저는 접속됨" → chrome-devtools-mcp로 직접 확인: 페이지 무한 busy, 네트워크 XHR 비어있음, 스크린샷 timeout. **페이지 껍데기만 200, 데이터 API 모두 죽음** 확정

### 처리
- ZDM: 차단 (정보팀 호출 필요. 복구 후 daily-routine 재실행으로 누락 보정 자동)
- MES 단독 진행 (사용자 명시 "mes만 진행"):
  - daily-routine `run_mes()` 단독 호출 (production-result-upload/run.py는 9223 CDP 의존 + 자동 로그인 미구현이라 daily-routine 측 직접 HTTP OAuth 사용)
  - 누락일 2026-04-28 (1건) 업로드 성공: 15/15건, qty 45,381/45,381 BI 일치

### [C] mes_login() 패치
- 원인 가설: 1차 POST 매번 500 → cookies.get("XSRF-TOKEN") 빈 값 의심
- 패치 1줄: `mes_login()` return 직전 `layout.do` GET 1회 추가
- 검증: 다음 daily-routine 실행 시 1차 시도 성공 여부 추적
- 가설 미통과 시 `git revert` 1회로 즉시 롤백 가능 (read-only GET 추가만)

### Chrome 디버그 포트 켜둠 (다음 세션 재사용 가능)
- 9222: `C:/temp/chrome-debug` (ZDM 진단용)
- 9223: `C:/temp/chrome-mes` (MES OAuth용)

### TASKS.md 아카이브 분리 (사용자 명시 1번 옵션, daily-doc-check 후속)
- 사용자: STRONG 임계(800줄) 초과 → "지금 정리" 옵션 선택
- 세션105~108 (4개 가장 오래된 세션, 약 278줄) → `98_아카이브/TASKS_archive_세션105-108_20260429.md` 분리
- 결과: TASKS.md 874→598줄 (-276줄). 임계 [STRONG] → [WARN]
- 백업: `TASKS.md.bak_session128` (gitignore)

### 다음 AI 액션
- ZDM 서버 복구 확인 후 daily-routine 재실행 → 4/29 + 4/29 ZDM 누락 보정 동시 처리
- 다음 MES 업로드 시 1차 시도 성공 여부 로그 확인 → 패치 효과 검증

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
