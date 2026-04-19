# HANDOFF — AI 인수인계 문서 (세션 메모 전용)

> **이 파일은 세션 인수인계 메모다. 상태 원본이 아니다.**
> 작업 완료/미완료 판정은 TASKS.md 기준. 이 파일이 TASKS와 충돌하면 TASKS를 따른다.
> 세션 변경사항과 다음 AI 액션만 기록한다. 완료/미완료를 독립 선언하지 않는다.

최종 업데이트: 2026-04-19 KST — 세션74 (쟁점 G settings 계층 실물 분리)
읽기 순서: **TASKS.md → STATUS.md → HANDOFF.md** → CLAUDE.md → 도메인 CLAUDE.md

---

## 0. 최신 세션 (2026-04-19 세션74 — 쟁점 G 실물 분리)

### 이번 세션 계획
세션73 이월 1건:
1. 쟁점 G settings 계층 실물 분리 (단일 원자 커밋 + 세션 재시작 필수)

### 완료 — 단일 원자 커밋으로 settings 분리

**변경 요약**:
- `.claude/settings.json` 신설 (신규 Git 추적): TEAM 76 permissions + hooks 31매처 + statusLine
- `.claude/settings.local.json` 축소: PERSONAL 8 + ask 8 (hooks/statusLine 제거)
- 제거 18건: 개인경로 11 + 1회용 잔재 7 (탭 URL echo 2·PID echo 2·JSON 1회용 검증 1·하드코딩 슬랙 2)
- `.claude/hooks/permissions_sanity.sh` single-quote regex 버그 수정 (6/6 단위 검증)
- `.gitignore` 2개 라인 추가: `!.claude/settings.json` + `.claude/settings.local.json.bak_20260419`
- **검증 스크립트 5개 team+local union 지원 (근본 해결, 커밋 도중 발견)**: `final_check.sh` SETTINGS 분리 + registered_hook_names union, `smoke_test.sh` grep helper + 5곳 전환, `smoke_fast.sh` 양쪽 JSON 검증, `doctor_lite.sh` 루프 검증, `permissions_sanity.sh` union allow 스캔. 세션71 정책 누락(검증 스크립트 하드코딩 미교정) 해소.
- `90_공통기준/업무관리/STATUS.md` 세션74로 갱신

**검증**:
- smoke_fast 9/9 PASS · doctor_lite OK · permissions_sanity 경고 0건
- hooks 구조 원본 vs 신설 diff 완전 동일
- PreToolUse 16매처 순서 100% 보존 (block_dangerous 첫째)
- JSON 파싱 양쪽 유효 (settings.json allow=76 · settings.local.json allow=8)

**주의 사항**:
- `.claude/settings.local.json`은 **이미 Git 추적 중**인 기존 정책. 본 커밋에도 변경분 포함. `.gitignore` line 39의 `.claude/settings.local.json` 제외 라인은 추적 중 파일에는 무효지만 향후 untracked 상태 대비 보험으로 유지.
- `Read(//c/Users/User/...)` 절대경로 권한은 TEAM `Read` 기본 권한이 있으므로 DELETE 대상에 포함됨 (기능 손실 없음).

### 다음 세션 첫 액션 — **사용자 수행 필수**

1. **Claude Code CLI 종료 → 재실행** (settings 캐싱 특성상 재시작 없이 새 설정 미반영)
2. 재시작 후 새 세션에서 순서대로 검증:
   - `bash .claude/hooks/doctor_lite.sh` → OK
   - `bash .claude/hooks/smoke_fast.sh` → 9/9 PASS
   - `bash .claude/hooks/permissions_sanity.sh` → 경고 0건
   - 임의 Bash 호출 시 `block_dangerous` trigger 확인 (PreToolUse 첫 매처 동작)
3. 이상 시 롤백 절차: `C:\Users\User\.claude\plans\cryptic-tinkering-ladybug.md` Case B/C 참조
4. 1주 후 permissions 팝업 빈도 측정 (분리 효과 확인)

### 이월 (세션75+)
- `hook_timing.jsonl` 1주 집계 + gate 9개 `exit 2` 승격 판단
- `debate_verify` 태그 incident 7일 0건 달성 시 Phase 2 승격

---

## 0-prev. 세션73 (2026-04-19)

### 이번 세션 계획
세션72 이월 3건:
1. GPT 지적 A — PreToolUse JSON 필드 `hookSpecificOutput` 스키마 마이그레이션
2. Phase 2-C timing 배선 (25개 훅)
3. 쟁점 G settings 계층 실물 분리 **사전작업** (실물 분리는 세션74)

### Step 1 완료 — PreToolUse JSON 스키마 마이그레이션 (스코프 확장)
- context7(/anthropics/claude-code) hook-development SKILL 기준으로 PreToolUse **12개 훅 20개 JSON 출력** 스키마 교체
- 스코프 확장 사유: 초기 5개 계획 → `smoke_test.sh` 46-3 검사가 구식 가정(`hookSpecificOutput 잔재 없음`) + PreToolUse gate 7개 누락 추가 발견 → 일관성 유지 위해 일괄 처리
- Phase 2-B 완료(exit 2 유지) 5개: `block_dangerous`(6) · `commit_gate`(2) · `date_scope_guard`(1) · `protect_files`(2) · `harness_gate`(2)
- 추가 PreToolUse gate 7개: `evidence_gate`(1) · `mcp_send_gate`(1) · `instruction_read_gate`(1) · `skill_instruction_gate`(3) · `debate_gate`(1) · `debate_independent_gate`(1) · `navigate_gate`(1)
- `smoke_test.sh`·`e2e_test.sh` 갱신: grep 패턴 양식 병행 허용(10건) + 46-3 assertion 뒤집기
- Stop 이벤트 훅(`stop_guard`, `gpt_followup_stop`, `completion_gate`, `evidence_stop_guard`)은 legacy 형식 유지
- 20/20 JSON 파싱 유효 + smoke_fast 9/9 PASS + doctor_lite OK + final_check `FAIL 0` 달성

### Step 2 완료 — Phase 2-C timing 배선 (25개 훅)
- measurement 11 + advisory 5 + gate 9 훅 `hook_timing_start`/`hook_timing_end` 배선
- status 태그 세분화 (pass/skip_*/block_*/warn/compile_ok 등)
- gate exit 2 승격은 1주 수집 후 판단 — 커밋 C 문서에 기준선 기록
- 검증: smoke_fast 9/9, doctor_lite OK, final_check 167/167 PASS

### GPT 판정 PASS (845e2e93) — 세션73 마감
- 3커밋 모두 실물 검증 통과. 세션72 HANDOFF 3건 전부 충분히 처리됨 판정
- 스코프 확장 5→12훅 타당 (smoke_test 46-3 구식 가정 + 누락 7개 발견)
- 쟁점 G 사전작업 세션74 실행 전제 충분
- 하네스 분석: 채택 4건 / 보류 0건 / 버림 0건

### Step 3 완료 — 쟁점 G 사전작업 문서
- `90_공통기준/토론모드/session73_review19_decisions.md` 신설
- Permissions 100건 재분류: TEAM 80 / PERSONAL 4 / 개인경로 11 / DELETE 3
- 부수 발견: `permissions_sanity.sh` single-quote 미탐지 버그 — 세션74 수정 검토
- gate 9개 exit 2 승격 절차 문서화 (1주 hook_timing.jsonl 수집 후)
- 세션74 실물 분리 6단계 + 롤백 전략 명문화

### 다음 세션 첫 액션
1. **세션74**: 쟁점 G 실물 분리 (단일 원자 커밋 + 세션 재시작 필수)
   - settings.json 신설 80건 + hooks 31 + statusLine
   - settings.local.json 축소 (PERSONAL 4 + 개인경로 11)
   - DELETE 3건 제거, `permissions_sanity.sh` regex 버그 수정 포함 가능
   - 재시작 후 doctor_lite + smoke_fast + permissions_sanity 순 검증
2. **세션75**: `hook_timing.jsonl` 1주 집계 + gate 9개 exit 2 승격 판단
3. **조건부**: `debate_verify` 7일 0건 달성 시 Phase 2 승격

---

## 0-prev. 세션72 (2026-04-19)

### 이번 세션 완료
1. **Phase 2-B Step 1 — `completion_gate.sh` 소프트 블록 추가**:
   - 최근 7일 `permissions_sanity` 1회용 라벨 3회 이상 누적 시 deny 1회 (60초 쿨다운, 하드페일 없음)
   - 상위 게이트 통과 후에만 평가 → 기존 동작 불변
2. **Phase 2-B Step 2a — `commit_gate.sh` exit 2 전환**:
   - 모든 종료 경로에 `hook_timing_end` 배선
   - `block_marker`/`block_final_check` 경로에 `exit 2` 승격 (JSON deny + exit 2 병행)
3. **Phase 2-B Step 2b — `debate_verify.sh` Phase 2 승격 보류**:
   - `incident_ledger` `debate_verify` 태그 18건 잔존(result.json/step5 반복 누락) → Phase 2-C 재평가
   - 현 세션: timing 배선만 추가
4. **Phase 2-B Step 3 — 핵심 훅 5종 timing + exit 2 전환**:
   - `block_dangerous.sh`/`date_scope_guard.sh`/`protect_files.sh` exit 2 승격
   - `evidence_stop_guard.sh`/`stop_guard.sh` 기존 exit 2 유지 + timing 배선
5. **문서 갱신**:
   - `.claude/hooks/README.md` 등급 테이블 Phase 2-B/2-C 2단 재구성
   - `CLAUDE.md` 훅 등급 정책 섹션 "현재 실코드 상태"를 "Phase 2-B 적용 현황"으로 치환

### 블로커 기록
- `debate_verify.sh` Phase 2 승격 — incident 18건 잔존. 승격 보류 결정. Phase 2-C 재평가 조건: 7일 연속 0건

### 검증 결과
- `smoke_fast.sh` 9/9 PASS
- `doctor_lite.sh` OK
- `permissions_sanity.sh` 경고 0건 (캐시 제거 후 재실행)
- `hook_timing.jsonl` 다중 훅 status 태그 정상 기록
- **GPT 판정 PASS** (fb58b9b2) — 3쟁점 타당성 확인 완료. hook_gate 미사용/60초 쿨다운/7일 0건 조건 모두 PASS. 후속 과제 2건(JSON 필드 마이그레이션·소프트블록 로그 보강)은 FAIL 사유 아님.

### 하네스 분석 (GPT 판정 응답)
- 채택 2건: 지적 A(JSON 필드 deprecated→hookSpecificOutput 표준화), 지적 B(소프트블록 확인 흔적 보강 후속 제안)
- 보류 1건: debate_verify 대체 조건 "10회 연속 clean" — 현 시점 변경 불필요, Phase 2-C 진입 시 재평가
- 버림 0건
- 독립 견해: JSON 필드 마이그레이션은 context7로 최신 spec 확인 선행. 소프트블록 로그 보강은 실제 3회 누적 발생 후 설계 (예방적 과잉설계 회피).

### 다음 세션 첫 액션
1. **세션73**: 쟁점 G settings 계층 실물 분리 (settings.json 이동) + Phase 2-C 나머지 훅 일괄 배선 + GPT 지적 A(JSON 필드 표준화) context7 조사
2. **세션74**: 의제6 Gemini 진입 강제 hook 신설
3. **세션75**: 의제7 탭 throttling 자동 회복
4. **조건부**: `debate_verify` 태그 7일 0건 시 Phase 2 exit 2 승격

---

> **이전 세션 이력 아카이브**: `98_아카이브/handoff_archive_20260418_20260419.md`
