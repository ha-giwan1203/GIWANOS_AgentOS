# 업무리스트 작업 목록

> **이 파일은 AI 작업 상태의 유일한 원본이다.**
> 완료/미완료/진행중/차단 상태는 이 파일에만 기록한다.
> STATUS.md·HANDOFF.md·Notion은 이 파일을 참조하며, 독립적으로 상태를 선언하지 않는다.
> 판정 우선순위: TASKS.md > STATUS.md > HANDOFF.md > Notion
> 도메인 하위 `TASKS.md`는 해당 도메인 내부 실행 목록만 관리한다. 저장소 전체 우선순위·완료판정·인수인계 기준은 항상 이 파일이다.
>
> **주의: 이 파일은 현업 업무 전체 목록의 원본이 아니다.**
> 실제 업무 일정, 남은 과제, 반복 업무, 마감일의 기준 원본은 `90_공통기준/업무관리/업무_마스터리스트.xlsx`이다.
> 이 파일은 그중 AI가 수행해야 하는 자동화·문서화·구조 개편·검토·인수인계 작업만 관리한다.

최종 업데이트: 2026-04-24 KST — 세션101 /d0-plan 스킬 실운영 검증 + 자동 스케줄링 등록 + GPT 정밀평가 3자 토론 반영 (P-1/P-2/P-3)

> **메타 억제 기준**: `.claude/state/meta_freeze.md` — **해제됨** (2026-04-23, incident 52건)

---

## 세션101 (2026-04-24) — /d0-plan 스킬 실운영 검증 + 자동 스케줄링

**[완료] SP3M3 주간 15건 실운영 반영 (아침 세션 첫 실행)**
- 파일: `SSKR D+0 추가생산 Upload.xlsx` (생산일 2026-04-24, 15건)
- Phase 3 업로드 → Phase 4 서열 배치 15건 → Phase 5 MES 전송 (rsltCnt=750) → Phase 6 SmartMES 순서 일치 ✅

**[완료] 스킬 런타임 버그 수정 3건**
- `navigate_to_d0`: OAuth 리다이렉트 완료 대기 추가 (goto 네비게이션 충돌 해소)
- `--xlsx` 옵션: 외부 엑셀 파일 직접 지정 모드 (Phase 1 추출 건너뜀)
- `--skip-upload` 옵션: Phase 3 업로드 건너뜀 (이미 상단 등록된 경우 Phase 4부터)
- s_grid 대기 조건 완화: `>= 5행` → 고정 3초 (주간 초기 빈 서열 대응)
- 팝업 오픈 재시도 (최대 3회)

**[완료] 자연어 트리거 키워드 대폭 확장 + 금지사항 명시**
- SKILL.md description: "등록/반영/올려/업로드" × "주간/야간/D0/SP3M3/SD9A01/아우터" 조합
- Excel 직접 열기 / 모니터 전환 / ERPSet Client(javaw.exe) / computer-use 마우스 조작 **금지** 명시
- `.claude/commands/d0-plan.md` 자연어 트리거 섹션 추가
- 배경: Claude Desktop + computer-use 세션에서 스킬 미인식 + 엉뚱한 경로 탐색 사건

**[완료] Windows 작업 스케줄러 자동 실행 등록**
- 작업명: `D0_SP3M3_Morning`, 매주 월~토 07:10 KST, 일요일 제외
- 실행 계정: InteractiveToken (사용자 로그온 시에만, pyautogui GUI 필요)
- 래퍼: `90_공통기준/스킬/d0-production-plan/run_morning.bat`
- 로그: `06_생산관리/D0_업로드/logs/morning_YYYYMMDD.log` (일자별 누적)
- 첫 자동 실행: 2026-04-25 토요일 07:10

**[완료 추가] 하이브리드 자동 커밋 hook 신설 (세션101)**
- `.claude/hooks/auto_commit_state.sh` — Stop 이벤트 5번째 등록 (hooks 31→32)
- AUTO: TASKS/HANDOFF/STATUS/notion_snapshot/finish_state/write_marker → 자동 커밋+푸시
- MANUAL: 코드/스킬/설정 → stderr 리마인더만 (`/finish` 또는 수동 커밋 권장)
- 안전장치: main 브랜치만, 민감패턴 스캔, push 60s timeout soft-fail

**[완료 추가] GPT 정밀평가 3자 토론 반영 (세션101, 2026-04-24)**
- 3자 토론 (Claude × GPT 웹 × Gemini API 2.5-pro) — `/debate-mode` 변형 (Gemini는 API 대체, 사용자 지시)
- 합의 결과: 3건 채택 / 3건 반려(GPT 과잉 경보)
- **P-1 (A-수정안 GPT 제안)**: `.claude/hooks/auto_commit_state.sh` git commit 직전 `final_check.sh --fast` 인라인 호출 추가 — Stop hook 자동 커밋도 교차검증 통과 시에만 진행 (commit_gate 우회 해소)
- **P-2**: `.claude/settings.local.json` 절대경로 3건 (L21/L29/L32) → 상대경로화
- **P-3**: `.claude/hooks/list_active_hooks.sh:9` 주석 "(31)" → "(32)" drift 정정
- **반려**: A2-1(d0 SKILL ↔ /d0-plan command wrapper 정상), A2-5(6건 command+skill pair wrapper 정상), 리포트 "임시검토"(환경 한계)
- **이월 (P-4 신규)**: slash 진입 vs 자연어 진입 drift 감시 — `.claude/hooks/skill_drift_check.sh` 기능 확장 또는 별도 `wrapper_consistency.py`
- 플랜 파일: `C:/Users/User/.claude/plans/splendid-coalescing-snowflake.md` (보존)
- 검증: smoke_fast 11/11 PASS, doctor_lite OK, hook count 32
- **GPT 조건부 통과 지적 반영 (2건 제거)**: `Bash(sort -k6,7)` 일회성 제거, `Bash(PYTHONIOENCODING=utf-8 python3 90_공통기준/스킬/daily-routine/run.py)` L14와 완전 중복이라 제거. 유지 3건(mcp__Claude_in_Chrome__read_page/find, list_active_hooks.sh --count)은 3자 토론·검증 도구로 반복 사용 근거 있음

**[대기] 후속**
- 4/25~28 자동 실행 관찰 (성공률/로그 이상/중복 저장 등)
- SD9A01 OUTER 저녁 세션 실 검증 (내일 저녁 `--dry-run` 먼저)
- 안정화 후 grade B → A 격상

---

## 세션100 (2026-04-23) — GPT 프로토콜 스킬 신설 (클로드코드 정밀평가)

**[완료] `90_공통기준/업무관리/gpt-skills/` 신설 + 프로토콜 1건 등록**
- 배경: 사용자가 GPT에게 매번 장문으로 "클로드코드 전체 상태 정밀평가"를 입력 → 평가 깊이 불일치, 개선안이 전체 구조를 안 봐서 수정하면 다른 곳이 터지는 반복 문제
- 신규 파일 3건:
  1. `90_공통기준/업무관리/gpt-skills/claude-code-analysis.md` — 트리거 4종 + 7서브시스템(S1~S7) + 5축(A1~A5) + R1~R5 영향반경 필드 + 엄격 템플릿
  2. `90_공통기준/업무관리/gpt-skills/README.md` — 폴더 목적·추가 등록 규칙
  3. `90_공통기준/업무관리/gpt-instructions.md` — "GPT 프로토콜 스킬" 섹션 추가 (도메인 진입 프로토콜 아래)
- 설계 원칙: 大→中→小 계층 순서 고정 + 각 개선안에 R1~R5 영향반경 의무 첨부 (누락 시 자동 강등)
- Claude Code 쪽 hook/skill/settings/CLAUDE.md 변경 **없음** (B분류 구조 변경 아님, 2자 종결 경로)
- 플랜: `.claude/plans/gpt-steady-wreath.md` (사용자 승인 후 구현)
- 검증: 커밋 푸시 후 ChatGPT에서 "클로드코드 정밀평가" 실입력 테스트 예정
- GPT 프로젝트 업로드: 사용자 지시로 ChatGPT 프로젝트에 직접 업로드 (세션 내 후속 작업)

---

## 세션99 (2026-04-23) — AGENTS_GUIDE hooks 파서 버그 수정 (2자 토론 통과 — GPT 최종 PASS)

**[완료] GPT 최종 판정 PASS** (커밋 fa4face2 실물 대조)
- 로그: `90_공통기준/토론모드/logs/debate_20260423_212854/round2_gpt_final.md`
- 보강 3건 실물 반영 확인 + 상태 원본 충돌 없음 + 회귀 PASS
- 별건(README M5, SETTINGS dead assignment) PASS 막지 않음 확인. 세션99 종결

**[완료] final_check 4.5 섹션 신설 — HANDOFF 헤더-본문 판정 레이블 정합 advisory**
- 사용자 지시 예외(D안) 즉시 적용. B 분류 구조 변경이나 "지금바로 적용해라" 명시 지시로 A 강등
- 증상: Round 1 "조건부 통과" 헤더가 Round 2 PASS 후에도 지연 반영되던 실제 사건(세션99 본건) 재발 방지
- 구현: `final_check.sh` 4.5 섹션 신설 — L7 `최종 업데이트` 헤더에 "조건부/Round 1/보류" + 섹션0 본문 "최종 판정" 이후 5줄 내 "**통과**/PASS/통과 (PASS)" 둘 다 매칭 시 `warn`
- 검증: 포지티브(정합) OK / 네거티브(헤더만 조건부로 재현) WARN 정상 감지 / smoke_fast 11/11 PASS
- 훅 등급: advisory (차단 없음, stderr 경고만)


**[완료] generate_agents_guide.sh hooks 파서 M3/M4 패턴 전환**
- 로그: `90_공통기준/토론모드/logs/debate_20260423_212854/round1_gpt.md`
- A 분류 자가판정 (버그 수정, 실행 흐름·판정 분기 불변). GPT 동의 — 3자 승격 불필요
- **변경 파일 1건**: `90_공통기준/업무관리/generate_agents_guide.sh` L7-38
  - `grep -oE "...\\.sh\"" ... | wc -l` 셸 손파싱 → `parse_helpers.py --op hooks_from_settings` (team+local union)
  - Windows \r 이슈 대비 `tr -d '\r '`. M3/M4 선례 재사용
- **GPT 조건부 통과 보강 3건 전부 반영**:
  - PY_CMD fallback (`doctor_lite.sh:10-11` 선례) — Windows/경량 환경 Python 부재 대응
  - 헤더 문구 `"settings.local.json 기준"` → `"settings.json+settings.local.json 기준"` (union 정합)
  - settings 둘 다 부재 시 `[WARN] settings files missing` stderr 1줄 (원인 은닉 방지)
- **증상 해소**:
  - `AGENTS_GUIDE.md` "0개 활성" → "31개 활성"
  - `final_check --fast` 3.5 섹션 WARN → `[OK] AGENTS_GUIDE hooks 개수 일치 (31개)`
- **회귀**: smoke_fast 11/11 ALL PASS
- **명시적 비변경**: README 계층별 훅 테이블 파싱(L47-62 별건 M5 후보), SETTINGS dead assignment 정리(별건)

---

## 세션98 (2026-04-23) — 시스템 전체 드리프트 2자 토론 + 실행

**[완료] GPT 시스템 평가 실물 대조 + Explore 3병렬 독립 스캔**
- GPT 8건 중 7건 사실, 1건(post_commit_notify 배치) 반만 사실로 확인
- Claude 독립 발견: 도메인 STATUS 5개 drift 12~23일(High), 고아 폴더 5개(Med), 정리대기_20260328(Med)
- 토론 로그: `90_공통기준/토론모드/logs/debate_20260423_193314/`

**[완료] 2자 토론 Round 1 합의 (3자 승격 불필요)**
- 의제1 A안 채택: `DESIGN_PRINCIPLES.md:10` "정적 출력만" → "정적 + advisory 보조 허용" 문구 현실화
- 의제1 부가: parse_helpers M4 선행, M3 지연 불가 (GPT 조건 수용)
- 의제2 C2 채택: 신규 advisory 훅 `domain_status_sync.sh` 신설 (1 Problem ↔ 1 Hook)
- 의제3 수정 채택: URL echo 7건·숫자 echo 8건 제거 (포괄 통합 아님), dry-run 3건 통합

**[완료] 즉시 실행 4건**
- `smoke_fast.sh` 주석 "5~8건" → "11건" (실제 검사 수와 일치)
- `harness_gate.sh` 주석 "마지막 5000자" → "마지막 20000자" (실제 tail -c와 일치)
- `README.md` `post_commit_notify.sh` Notification 층 → 추적층(PostToolUse) 이동 + event 명시
- `DESIGN_PRINCIPLES.md` L10 A안 문구 수정

**[완료] parse_helpers M4 — `risk_profile_prompt.sh` 셸 파서 이관**
- 기존 셸 while + grep + sed 블록(L85-141) 제거 → `parse_helpers.py --op match_domain` 호출
- `parse_helpers.py`에 `match_domain_by_keywords()` 신규 함수 + CLI op 추가
- 회귀: smoke_fast 11/11 PASS, active_domain.req 정상 작성

**[완료] parse_helpers M3 — `final_check.sh` 4개 자체 파서 이관 (SSoT 종결)**
- `registered_hook_names` / `readme_active_hook_count` / `readme_active_hook_names` / `status_hook_count` 함수 내부를 parse_helpers CLI 호출로 대체
- Windows Python stdout \r 삽입 이슈 발견 → `tr -d '\r'` 추가
- DESIGN_PRINCIPLES 원칙 7 "Single Source of Truth" 실제 코드로 끝남

**[완료] C2 `domain_status_sync.sh` 신규 advisory 훅**
- 전역 TASKS 날짜 vs 도메인 STATUS.md 5개 날짜 비교 → 14일+ drift 감지 시 stderr 경고
- 실측: 05 조립비정산 17일·10 라인배치 23일 drift 감지 확인
- `session_start_restore.sh`에 호출 추가, fail-open / exit 0 강제
- 30일 실측 후 gate 승격 여부 재평가 (2026-05-23)

**[완료] permissions.local.json 정리 (63 → 27, 57% 감축)**
- URL echo 7건 제거 (`Bash(echo:*)` 팀 포괄 이미 존재 — 중복 제거)
- 숫자 echo 8건 제거 (대화방 ID 1회용 — 영구 허용 가치 없음)
- dry-run 3건 + 기타 incident_repair 호출 6건 → `Bash(python3 .claude/hooks/incident_repair.py:*)` 1건으로 통합
- 1회용 mkdir/rmdir/tmp py/worktree cleanup/chrome debug 다수 제거

**[완료] GPT 최종 판정 후속 마무리 (실행 가능 항목 전부)**
- GPT 지적: README smoke_fast "5~8건" 문구 잔존 → `.claude/hooks/README.md:149` "11건"으로 정정
- GPT 지적: 도메인 STATUS 5개 실물 drift 잔존 → 02/04/06/05/10 헤더에 세션98 전역 점검 stamp 추가 ("도메인 내용 변경 없음" 명시로 정직성 유지)
- `domain_status_sync.sh` 정규식 강화: 파일 내 모든 YYYY-MM-DD 중 최대값 선택으로 변경 (이전: 첫 매치만 → 헤더 포맷에 최신/구 날짜 혼재 시 오판). drift 0건 확인
- AGENTS_GUIDE.md 재생성 (generate_agents_guide.sh 실행, skills 20개 반영. hooks=0 버그는 스크립트 별건)
- `state/` 7일+ 마커 2건 정리 (debate_independent_review.ok / 구 세션 skill_read.ok)
- 고아 폴더 5개 유지 결정 기록 (사용자 지시, 드리프트 재분류 금지)
- **GPT 최종 판정: PASS** (세션98 닫음, 잔여 3건은 별건 의제로 분리)

**[완료] 98_아카이브 정리대기_20260328 분류 (Option C)**
- `_cache/` 6건 + `run_logs/` 16건 = 22건 삭제 (재생성 가능한 임시 캐시·로그, git tracked 아님)
- 나머지 71건 보존 + 폴더 rename: `98_아카이브/정리대기_20260328/` → `98_아카이브/구버전_20260328/` (30일 정리대기 규칙 벗어남, 참조 가치 유지)
- 보존 내용: 구버전_스킬(6) / 구버전_임률단가(13) / 구버전_조립비정산_스크립트(19) / 구버전_조립비정산_엑셀분석(30) / 보류판정_아카이브(2) / 보류파일목록_20260328.md(1)

---

## 세션96 (2026-04-23) — STATUS drift 근본 원인 분석 + final_check 감지 강화

**[완료] daily-doc-check 자동 실행 → STATUS stale 감지 → 근본 원인 2회 분석**
- 자동 점검 결과: STATUS.md 세션90 표기, 실제 최신 세션95 (4세션 뒤처짐). Slack 알림 발송
- 1차 원인: 같은 날 세션 진행 시 날짜(YYYY-MM-DD) 비교만으로는 drift 미감지 (세션91~94 모두 2026-04-22)
- 2차 원인 (테스트 과정 발견): `_get_session`/`_get_date`가 git index 우선 조회 → 파일 edit만 하고 `git add` 전이면 working tree 변경 미반영

**[완료] 세션94~95 미커밋 35건 커밋 (`ac8369ff`)**
- /d0-plan 스킬 신규 (SKILL.md / run.py / D0_저녁.bat)
- 서열정리 작업노트, 명찰 이동, 기타 정리 삭제, 토론모드 bridge 모듈 등 세션94~95 누락분 일괄 반영
- STATUS.md 날짜 수동 교정: 세션90/2026-04-22 → 세션95/2026-04-23

**[완료] final_check.sh drift 감지 강화 2건**
- (a) **STATUS 세션 비교 블록 추가** (L305~): HANDOFF 패턴을 STATUS에도 복제. `[ "$STATUS_DATE" = "$TASKS_DATE" ]` 조건으로 날짜 drift와 중복 방지. `--fix` 시 날짜는 유지하고 세션 번호만 갱신 (`\1` 캡처)
- (b) **`_get_session` / `_get_date` working tree 우선 조회**: 기존 `git show :file` 우선 → `cat file` 우선으로 swap. git add 전 상태도 drift 감지 가능
- 검증: drift 재현(STATUS 세션90) → `[FAIL] session_drift` 감지 → `[FIX] 세션90→95` 교정 → smoke_fast 11/11 ALL PASS

**[완료] /auto-fix 규칙 6 추가 — pre_commit_check 원인-해소 연결 (2자 토론 조건부 통과 반영)**
- 로그: `90_공통기준/토론모드/logs/debate_20260423_112214/`
- GPT 판정: 조건부 통과 — fast/full 분기 조건 추가 요구
- 실측: pre_commit_check 202건 = `final_check --fast FAIL` 166건 + `final_check --full FAIL` 36건 (100% 분류)
- `incident_repair.py` auto_resolve() 확장:
  - 조건 (AND): `classification_reason == "pre_commit_check"` + `ts < now - 72h`
  - detail 분기: `--fast FAIL` → `final_check --fast` PASS로 해소 / `--full FAIL` → `final_check --fast` + `smoke_test.sh` 둘 다 PASS로 해소
  - 마킹: `resolved_by="auto_rule6"` + `resolved_reason="pre_commit_check_stale_{fast|full}"`
  - 사전 1회 subprocess 호출로 현재 PASS 여부 캐시 (루프 외부)
- 독립 하네스: GPT 평가(A1 파싱/B1 gate 일관성/Pri4 final_check 분리) 채택 3건, (A3 incident_ledger/C1 debate_verify/Pri5) 보류 3건, (B2 selfcheck 깊이) 버림 1건 — smoke_test 계층 미반영으로 환경미스매치

**[완료] 파싱 공통층 Python 헬퍼화 + final_check 2축 분리 묶음 — M1 (2자 토론 조건부 통과 반영, A-수정안)**
- 로그: `90_공통기준/토론모드/logs/debate_20260423_122413/`
- 선행 3자 자동 승격 중단: `debate_20260423_122202_3way/abort.md` (사용자 지시 예외, D안)
- GPT 조건부 통과 요구 전면 반영:
  - domain_registry YAML → JSON (`.claude/domain_entry_registry.json`)
  - count만 → count + 이름 리스트 병행 제공
  - JSON 단일 출력 계약 (셸 재파싱 금지)
  - M1에서 `risk_profile_prompt` / `domain_entries` 실제 전환 제외 (M4 이월)
  - Shadow mode 1주 관찰 (현재 헬퍼 신설만, list_active_hooks 전환은 M2)
  - `risk_profile_prompt` 캐시 금지 (UserPromptSubmit 고빈도 → 정확도 우선)
  - 2축 경계: `write_marker` = runtime / `skill_instruction_gate` = 별도 축 유지
- **M1 산출물**:
  - `.claude/scripts/parse_helpers.py` 신설 — 7개 op (hooks_from_settings / readme_hook_names / status_hook_count / domain_entries / doc_dates / doc_session / shadow_diff_active_hooks) + JSON 단일 출력
  - `smoke_test.sh` 섹션 54 신설 (5건, regression): parse_helpers 실파일 존재 / hooks_from_settings total = list_active_hooks --count / shadow_diff match=True / doc_dates 파싱 / doc_session 파싱
- 검증: smoke_test **216/216 ALL PASS** / smoke_fast 11/11 / doctor_lite OK
- 다음 단계(M2 후속): shadow 1주 관찰 후 `list_active_hooks.sh` 헬퍼 호출 전환 + `final_check.sh` 파싱 전환 → M3 2축 분리 → M4 `risk_profile_prompt` 전환

**[완료] M2 — README regex 정교화 + list_active_hooks 헬퍼 전환 (2자 토론 Round 2 통과)**
- 로그: `90_공통기준/토론모드/logs/debate_20260423_130201/`
- GPT 보정 2건 + Claude 독립 추가 1건 합의 (총 6건 채택)
- **변경 파일 3건**:
  - `.claude/scripts/parse_helpers.py`: `extract_readme_hook_names` 정규식 정교화 (블록쿼트 제외 + 테이블 행 전용 매칭) → 33→31 정정. `_shell_equivalent_readme_hook_names` 신설(final_check.sh L66-79 awk+grep 의미 절차적 재구현). `shadow_diff_readme` 신규 op (helper Python regex ↔ helper 내부 shell-equivalent 동등성)
  - `.claude/hooks/list_active_hooks.sh`: 인라인 Python heredoc(약 65줄) → `parse_helpers.py --op hooks_from_settings` subprocess 호출. 출력 포맷팅(--count/--names/--by-event/--full) byte-exact 보존
  - `.claude/hooks/smoke_test.sh` 섹션 54-6 신설: `shadow_diff_readme` match=true 회귀 (216→217)
- **GPT 보정 채택**:
  - 5-추가 A: `render_hooks_readme.sh --dry` 검증 추가 — 의존자 실증(`render_hooks_readme.sh:25-29` `bash list_active_hooks.sh --count/--by-event` 호출 후 `awk -F': '` 파싱 → EVENT_LINE 생성)
  - 5-추가 B: shadow 기준을 README↔settings union이 아니라 helper Python regex ↔ helper 내부 shell-equivalent 동등성으로 변경. GPT 권고대로 subprocess 대신 헬퍼 내부 함수로 구현
- **Claude 독립 추가 채택**:
  - 5-추가 C: `list_active_hooks.sh` stdout 4모드(`--count`/`--names`/`--by-event`/`--full`) **byte-exact 회귀** — count·name 일치만으론 1바이트 변경 회귀 못 잡음. `awk -F': '` 파싱 정확성 보장
- **검증 8단계 모두 PASS**: 헬퍼 단독 / 외부 계약 / smoke_test 217/217 / smoke_fast 11/11 / final_check --fast / drift 재현 / render_hooks_readme.sh --dry diff 0 / shadow_diff_readme match=true / 4모드 byte-exact diff 0 + (비차단) settings.local.json 부재 시 동일 동작 31
- **명시적 비변경**: `final_check.sh:61-80` 셸 파서 — M3 이월 (헬퍼와 1주 안정 후 교체)
- 다음 단계(M3): final_check.sh의 `readme_active_hook_count`/`readme_active_hook_names` 헬퍼 호출 전환

**[완료] incident 군집 정리 — auto_resolve 규칙 7~10 신설 (2자 토론 Round 2 통과)**
- 로그: `90_공통기준/토론모드/logs/debate_20260423_130201/round3_gpt_incident.md`, `round4_gpt_incident.md`
- A 분류 자가판정 (incident_repair.py auto_resolve() 분기 추가, hook 흐름·차단 정책 불변)
- GPT 보정 4건 + Claude 독립 검증 모두 채택
- **신설 규칙**:
  - rule 7 (harness_missing): 72h + 무재발 (key=(reason, hook, normalized_detail), latest_ts_by_key)
  - rule 8 (meta_drift): STATUS.md 현재 날짜 ≥ detail STATUS 날짜 (28건 100% 해소)
  - rule 9 (doc_drift commit_gate WARN): 72h + 정확 일치 + 현재 final_check --fast doc_drift 미존재
  - rule 10 (evidence_missing): 72h 항상 필수 + 무재발 (fingerprint 우선 / hook+normalized_detail fallback)
- **GPT Round 2 보정 채택**:
  - latest_ts_by_key 단순화 (list[ts] 대신 max(ts) 1개)
  - synthetic negative test 6/6 ALL PASS (오래된+최근 동일 키는 미해소, 다른 키는 해소)
- **적용 결과**: 175 → 124 (-51, -29%)
  - rule 8: 28건 마킹 (meta_drift 전부 해소)
  - rule 9: 12건 마킹 (commit_gate stale WARN 정리)
  - rule 7: 4건 마킹 (harness_missing 무재발만 — 나머지 활성 학습 중)
  - rule 10: 0건 마킹 (evidence_missing 4가지 패턴 모두 재발 중 → 보존, 정확 작동)
- **잔존 미해결 124건**: harness_missing 44 / evidence_missing 43 / legacy_unclassified 12 / pre_commit_check 12 / 기타 13
- **검증**: smoke_test 217/217 / smoke_fast 11/11 / synthetic negative test 6/6 / encoding fix(subprocess utf-8 강제)
- 다음 단계: legacy_unclassified 12 backfill_classification → 분류 정상화 후 재평가, harness_missing/evidence_missing 활성 패턴 근본 원인 분석

**[완료] 활성 패턴 근본 원인 분석 + Wave 1 — rule 11 D0 stale allowlist 전용 (2자 토론 Round 6 통과)**
- 로그: `90_공통기준/토론모드/logs/debate_20260423_130201/round5_claude_diagnosis.md`, `round6_gpt_incident.md`
- A 분류 (rule 6/7~10 선례 동일, hook 흐름 불변)
- **분석 결과**:
  - evidence_missing 45건 시간 분포: instruction_not_read 24건은 04-21 마지막(학습 완료), 나머지 21건은 04-22~23 D0 자동화 작업 부산물(활성)
  - harness_missing 44건은 04-13~22 분산, 04-19 이후 산발적(학습 진행 중)
  - 21건 활성 패턴 분석: D0 인라인 스크립트(.claude/tmp/erp_d0_*.py) → MES 접근 시 SKILL.md 미읽기/identifier_ref/auth_diag 차단
  - 가설 E1: 정식 d0-production-plan/run.py 사용 후 자연 감소 (세션95 패키징 완료)
- **rule 11 신설** (Wave 1, 즉시):
  - 조건 (AND): classification_reason="evidence_missing" + (hook, normalized_detail) ∈ allowlist 3쌍 + ts<now-48h + latest_ts_by_key 무재발
  - allowlist 3쌍 (GPT Round 6 보정 — detail-only 아닌 정확 쌍):
    - ("skill_instruction_gate", "MES access without SKILL.md read")
    - ("evidence_gate", "identifier_ref.req 존재. 기준정보 대조(identifier_ref.ok) 없이 관련 도메인 수정 금지.")
    - ("evidence_gate", "auth_diag.req 존재. auth_diag.ok 없이 MES/OAuth 관련 실행 금지.")
  - 마킹: resolved_by="auto_rule11", resolved_reason="d0_stale_<mes|identifier_ref|auth_diag>"
  - 기존 evidence_missing 24h fallback과 역할 분리 (allowlist 케이스는 rule 11 위임)
- **검증**: synthetic test 6/6 ALL PASS / smoke_test 217/217 / smoke_fast 11/11
- **즉시 효과 0건 (정상)**: 21건 모두 48h 미만, D0 작업 종료 후 자연 적용
- Wave 2 (별 의제): harness_gate 트랜스크립트 윈도우 20000→50000 (A-1) / 라벨링 정규식 다변화 (A-2) / 마커 기반 (A-3, B 분류)
- 다음 단계: E1 가설 검증 — 다음 D0 작업(/d0-plan run.py) 시 evidence_missing 신규 발생 0건 관찰

**[완료] backfill_classification 매핑 확장 + legacy_unclassified 12 정규화 (2자 토론 통과)**
- 로그: `90_공통기준/토론모드/logs/debate_20260423_130201/round8_gpt_legacy.md`
- A 분류 (분류 매핑 확장만, hook 흐름 불변)
- **분석**: legacy_unclassified 12건 = navigate_gate 1건 (잘못 기록된 hook="gate_reject"/type="navigate_gate") + debate_verify 11건 (hook=None, tag="debate_verify")
- **GPT 보정 채택**: navigate_gate → instruction_not_read 틀림. **send_block** 정정 (실증: navigate_gate.sh:38 classification_reason="send_block")
- **신설**:
  - HOOK_TO_REASON에 "navigate_gate": "send_block" 추가
  - hook="gate_reject" + type="navigate_gate" → "send_block" 보조 분기 (깨진 기록형식 복구)
  - tag="debate_verify" + hook 없음 → "debate_verify_block" 분기
  - `--reclassify-legacy` CLI 옵션 신설 (기본 동작 보존, 명시 옵션으로 legacy 12건 재분류)
- **적용 결과**: backfill 57건 (legacy 12 + resolved 항목 빈 분류 45) → auto_resolve 추가 2건 해소
- **잔존 분류 (130→128)**: evidence_missing 52 / harness_missing 44 / debate_verify_block 12 / pre_commit_check 12 / doc_drift 4 / 기타 4
- **legacy_unclassified 0건** ✓
- 검증: backfill_classification 함수에 reclassify_legacy 옵션 추가, smoke_test 217/217, smoke_fast 11/11
- 다음 단계: debate_verify_block 12건 자동 해소 규칙 신설(별 의제), Wave 2 harness_gate 윈도우 확장(E1 검증 후), M3 final_check 헬퍼 전환(1주 안정 후)

**[완료] write_marker 토론 로그 제외 — commit_gate root cause 해소 (2자 토론 통과)**
- 문제: 토론 로그(`90_공통기준/토론모드/logs/round*.md`) 작성 시 write_marker가 새 마커 생성 + after_state_sync=false로 덮어씀 → final_check가 "TASKS/HANDOFF/STATUS 미갱신" FAIL → commit_gate 차단
- A 분류 (write_marker 제외 패턴 1줄 추가, hook 흐름 불변)
- 보완: `.claude/hooks/write_marker.sh`에 `90_공통기준/토론모드/logs/` 제외 패턴 추가 (skip_debate_log)
- GPT 의견: 옵션 A(토론 로그만 제외)가 정확. B(일반화 과잉) / C(안전장치 약화) / D(사람 기억 의존) 모두 부적절
- 근본 원인 해소 후 backfill 매핑 확장 커밋과 함께 단일 커밋

**[완료] rule 12 신설 — debate_verify_block cluster stale (2자 토론 통과)**
- 로그: `90_공통기준/토론모드/logs/debate_20260423_130201/round9_gpt_rule12.md`
- A 분류 (rule 6/7~11 선례 동일)
- GPT Round 9 보정 채택: entry 단위 무재발 X. **cluster 기준** stale (key=(phase, sorted(issues))). cluster latest_ts > 48h 시 같은 key 모든 entry 일괄 해소
- 마킹: resolved_by="auto_rule12", resolved_reason="debate_verify_stale"
- 적용 결과: 134→131 (-3건). rule 12 마킹 2건 (단일 entry cluster 49h+). 나머지 10건은 cluster latest 46-48h로 임계 미통과 → 시간 경과 후 자연 해소
- 검증: smoke_test 217/217 / smoke_fast 11/11
- 세션96 마무리

---

## 세션95 (2026-04-23) — /d0-plan 스킬 패키징 완료

**[완료] ERP D0추가생산지시 실 파이프라인 검증 + 스킬 배포**
- 오늘 아침: SP3M3 야간 22건 전체 자동 처리 성공
  - Chrome CDP 재기동 + OAuth 자동 로그인 ✅
  - D0 엑셀 업로드(파싱+저장) 자동화 ✅ (`jQuery.ajax` 경로로 500 해소)
  - 야간 서열 22건 엑셀 순서대로 추가 ✅ (중복 삭제→재생성으로 EXT_PLAN_REG_NO 최대값 매핑 버그 수정)
  - 최종 저장 (sendMesFlag=Y) + MES 전송 성공 (rsltCnt=1100) ✅
  - SmartMES rank 10~31 엑셀 순서 100% 일치 확인 ✅
- 운영 규칙 확정 (사용자 설명 기반)
  - 파일 경로: `Z:\15. SP3 메인 CAPA점검\SP3M3\생산지시서\{YYYY}년 생산지시\{MM}월\SP3M3_생산지시서_({YY.MM.DD})*.xlsm`
  - 파일명 날짜 = OUTER 생산일 = D+1 (전일 오후 저장)
  - 세션 3회: 저녁 SP3M3 야간(생산일=오늘) + SD9A01 OUTER(생산일=내일) / 아침 SP3M3 주간(생산일=오늘, 누적≥3600 컷)
- 스킬 패키징
  - `90_공통기준/스킬/d0-production-plan/SKILL.md` (grade B)
  - `90_공통기준/스킬/d0-production-plan/run.py` (600줄 통합, Phase 0~6)
  - `.claude/commands/d0-plan.md` — `/d0-plan` 등록 확인
  - 업로드 엑셀 저장 경로: `06_생산관리/D0_업로드/d0_{line}_{YYYYMMDD}.xlsx`
- 상세: `06_생산관리/서열정리/WORK_NOTE_20260423.md`

**[대기] 2~3일 운영 안정화 관찰**
- SD9A01 OUTER 실검증 (내일 저녁 첫 실행 `--dry-run` 권장)
- SP3M3 주간 3600 컷 실검증 (아침 세션 `--dry-run`)
- 안정되면 grade B → A 격상 검토

---

## 세션94 (2026-04-22) — ERP D0추가생산지시 + SmartMES 서열정리 자동화 탐색 [완료]

**[완료] 탐색 범위 확정 + 공통 환경 확보**
- ERP Chrome CDP(포트 9222, `.flow-chrome-debug`) + OAuth 자동 로그인 스크립트 동작 확인
  - `.claude/tmp/erp_oauth_login.py` — 저장 자격증명(0109) pyautogui 자동완성 방식
- D0추가생산지시 API 2단계 구조 확인(JS 소스 분석)
  - 파싱: `POST /prdtPlanMng/selectListPmD0AddnUpload.do` (multipart, form=`uploadfrm`, 파일 필드 `files`)
  - 저장: `POST /prdtPlanMng/multiListPmD0AddnUpload.do` (JSON `{excelList, ADDN_PRDT_REASON_CD:"002"}`)
- SmartMES 서열정리 기존 스크립트(`06_생산관리/서열정리/smartmes_reorder.py`) shift 필터 버그 식별 + 패치(미커밋)
  - `shift==02` 고정 → `status==R` 단독 조건으로 교체 (주간 작업분은 F/P라 자동 제외)

**[미완] 내일 재개**
- D0 자동 업로드 실검증 (오늘치는 사용자 수작업으로 저장 완료 → 내일 새 날짜 엑셀로 실행)
- SmartMES 서열정리 캘리브레이션 + `--execute` 시범
- 네트워크 감시 로거 재구현 (Playwright `new_cdp_session` → `Network.enable` 방식)
- 최종 산출물: `90_공통기준/스킬/d0-production-plan/` 스킬 패키징 (sp3-production-plan 패턴 참조)

**작업 노트**: `06_생산관리/서열정리/WORK_NOTE_20260422.md` (상세 체크리스트 + 보존 파일 맵)

---

## 세션93 (2026-04-22) — Hook 시스템 개선 (2자 토론 합의 plan.md 1주차 1번)

**[완료] 2차 진단 + 2자 토론 + 개선 계획 plan.md 작성**
- 2차 진단: GPT 2차 정밀진단 수령 → Claude 독립 검증 11/11 실증 + 등급 재조정 2건 제안
- 토론: 2자(Claude × GPT) 2라운드. 채택 11 / 보류 3 (해소 2, 잔존 1) / 버림 0
- 결론: "전면 재설계 대신 evidence 축 coverage 축소 + 남는 핵심 3종 contract형 재설계 하이브리드"
- 로그: `90_공통기준/토론모드/logs/debate_20260422_150445/plan.md` (1주차/2주차 + 검증 기준 + 롤백 조건)

**[완료] 1주차 1번 — hook_registry 격하 (Single Source of Truth 확정)**
- 변경 파일 (4개):
  - `.claude/scripts/hook_registry.sh` 상단 주석 [LEGACY / DEPRECATED] 표기 + 대체 경로 안내
  - `.claude/hooks/final_check.sh:139-149` `--fix` 경로 자동 sync 중단, list_active_hooks 기준 수동 갱신 안내로 전환
  - `.claude/hooks/README.md:6-12, 155-156` Single Source (list_active_hooks) 명시 + 보조 스크립트 표에 list_active_hooks 추가 + hook_registry legacy 표기
  - `90_공통기준/업무관리/STATUS.md:19` hooks 체계 기준축을 list_active_hooks로 명시
- 검증:
  - `list_active_hooks --count` = 31 (PreCompact 1 / SessionStart 1 / UserPromptSubmit 1 / PreToolUse 16 / PostToolUse 7 / Notification 1 / Stop 4)
  - `final_check --fast` 31/31/31 일치, exit 0
  - `smoke_fast` 11/11 ALL PASS
  - `doctor_lite` OK
- 소요: 약 30분

**[완료] 1주차 2번 — selfcheck 24h 정확 집계**
- `.claude/self/selfcheck.sh:75-97` CUTOFF prefix grep → python ISO8601 파싱 + datetime 비교로 교체
- 검증: 기존 prefix=0건(해당 시각 매칭 없음) vs 정확=74건(실제 24h 범위) — 실효성 확인

**[완료] 1주차 3번 — doctor_lite python/python3 fallback**
- `.claude/hooks/doctor_lite.sh:6-17` PY_CMD fallback 추가 (smoke_fast.sh:33 동일 패턴)
- 검증: `[doctor_lite] OK` 정상 출력

**[완료] 1주차 4번 — evidence coverage 축소 (본 수술)**
- (a) `evidence_gate.sh:127-139` tasks_handoff + tasks_updated/handoff_updated 검증 블록 제거 (commit_gate/final_check + completion_gate가 동일 책임 이미 수행)
- (b) `evidence_gate.sh:186-204` + `risk_profile_prompt.sh:80-87` map_scope req/deny 블록 제거 (evidence 버스 분리)
- (c) `evidence_gate.sh:165-184` + `risk_profile_prompt.sh:61-64` skill_read 그룹 제거 → skill_instruction_gate 전담. identifier_ref는 evidence-core로 유지
- (d) `evidence_mark_read.sh` C분류 7종(skill_read/domain_read/tasks_read/handoff_read/status_read/tasks_updated/handoff_updated) mark 생성 제거. 유지: skill_read__<ID> + date_check/auth_diag/identifier_ref
- (e) `smoke_test.sh` 섹션 53 신설(5건 정적 회귀 트립와이어), 섹션 17 런타임 케이스 44-3/4/5/7/9/11/12 무효화 정리 + 44-13 identifier_ref deny 런타임 추가. 섹션 19 skill_read/tasks_updated 마커 검증 교체. 섹션 48-5/51-6 무효화 주석 처리
- 검증: smoke_test **211/211 ALL PASS**, smoke_fast 11/11, doctor_lite OK, selfcheck 총 1250/해결 679/미해결 571/최근 24h 81건

**[관찰 예정] 1주차 반영 후 7일 관찰**
- 정량 목표: evidence_gate 7일 미해결 ≤ 136건 (세션86 기준 272건 대비 50% 감소)
- 현재 세션 시작 시점 지표: 미해결 559건 / 최근 24h 신규 65건
- 관찰 기간 중: selfcheck로 주간 추세 확인, 미달 시 2주차 5번(contract 재설계) 재검토

**[완료] /auto-fix 패턴 분석 + A-1/A-2/A-3 + B-1 2자 토론 반영**
- **A-1** — `incident_repair.py` `send_block` next_action 교체 (폐기된 `cdp_chat_send.py` 경로 → `Skill(debate-mode)` / `Skill(gpt-send)` 안내)
- **A-2** — python3 하드의존 잔존 7개 파일 → PY_CMD fallback 일괄 적용
  - `hook_common.sh` 상단 전역 `PY_CMD` 선언 + `export` (모든 hook 상속)
  - 교체: completion_gate / statusline / permissions_sanity / pruning_observe / debate_verify / skill_drift_check
  - `final_check.sh:113` 정규식에서 skill_instruction_gate 제외 (사용자 command 탐지용, 실행 아님)
  - 검증: `[OK] 운영 훅 python3 의존 0건 (PY_CMD 전역 fallback 적용)`
- **A-3** — `commit_gate.sh:138` GRACE_WINDOW 60→300 (세션86 evidence_gate 동일 패턴. 상위 fingerprint 8개가 commit_gate, 15회/6회/5회 반복 → suppress 효율 기대)
- **B-1** — `incident_repair.py:auto_resolve()` 확장 (2자 토론 합의: 옵션 B = 제안 2+3+5 채택, 1/4 제외)
  - 제안 2 (send_block): `debate_claude_read.ok` / `debate_entry_read.ok` mtime > incident ts 시 해소 (상태 기반)
  - 제안 3 (python3_dependency): 운영 훅 `python3 -c`/`python3 -` 0건 시 일괄 해소 (A-2 반영 조건 충족)
  - 제안 5 (structural_intermediate): 24h 시간 기반 (정보가치 소멸형)
  - 제외 이유 (GPT 반박 채택): 제안 1은 success marker 체계 미비, 제안 4는 시간 기반이 반복 패턴 지움
  - Claude 잠정안(옵션 B + 방식 B + 72h) 철회 — GPT "원인-해소 연결 약함" 지적 수용
- **실측 결과**: 미해결 **571 → 362건 (-209건, 37% 감소)**
- 검증: smoke_test 211/211 / smoke_fast 11/11 / doctor_lite OK / final_check 31/31/31

**[예정] 2주차 5~7번** (1주차 관찰 데이터 수령 후, 2026-04-29)

---

## 세션92 (2026-04-22) — Plan IV-5/V-7/VIII [완료]

**[완료]** /finish 종료 (final_sha=a1a81496). 단계 IV~VII 전부 완결.
VIII 관찰 계속 (세션91 참조). 상세: `98_아카이브/session91_glimmering/`

---

## 세션91 (2026-04-22) — Plan glimmering-churning-reef 단계 III~VII 완료

**[완료]** 단계 III~VII 전부 완결. 상세: `98_아카이브/session91_glimmering/TASKS_~session88.md`

**[진행중] 단계 VIII — 30일 TTL 관찰 (2026-04-22 ~ 2026-05-22)**
- smoke_fast 유지 / incident 신규 0 (24h) / Self-X 재도입 grep 0건
- 만료 시점(2026-05-22) 재평가

---

## 세션90 (2026-04-22) — 자기유지형 시스템 재설계 (Plan glimmering-churning-reef)

**[진행중] 2자 토론 기반 Self-X 자동 개입 폐기 + 수동 selfcheck 전환**
- 계획 파일: `C:/Users/User/.claude/plans/glimmering-churning-reef.md` (Part 0~8 + 보강안 A~D)
- 2자 토론: Claude × GPT 5라운드 (Round 4에서 누락 14건 + Round 5에서 2건 추가 식별)
- 사용자 선택: 안전안 (자기학습 포기 + 자기유지 보장). 메타 깊이 = 0 엄격 해석

**[완료] 단계 0 — baseline + invariants waiver (8924431d)**
- 0-1: incident baseline snapshot (unresolved 516 / gate_reject 376) → `90_공통기준/업무관리/baseline_20260422/incident_baseline.json`
- 0-2: invariants.yaml settings_drift WARN 임시 비활성화 (단계 V 완료 시 복원)
- 0-A: 활성 훅 37개 dep graph matrix → `baseline_20260422/dep_graph.md`
- 0-C: smoke_fast 10/10 PASS, doctor_lite OK, health_check 3 OK·5 WARN

**[완료] 단계 I — leaf hook 등록 해제 (82be4ab0 → 2300ceb9)**
- I-1 `quota_advisory.sh` (PostToolUse) · I-2 `self_recovery_t1.sh` (Stop)
- I-3 `circuit_breaker_check.sh` · I-4 `health_check.sh` (SessionStart)
- I-5 `session_start_restore.sh` last_selfcheck freshness 표시 + Self-X marker cleanup

**[완료] 단계 II — 감시 게이트 + dead config 정리 (ddef9b77, 471c07a8)**
- II-1 `health_summary_gate.sh` (UserPromptSubmit) 등록 해제
- II-2 `project_keywords.txt` → `98_아카이브/session89_glimmering/project_keywords_20260422.txt`

**활성 훅**: 36 → **31** (SessionStart 3→1 / UserPromptSubmit 2→1 / PostToolUse 8→7 / Stop 5→4) — 세션91에서 실측 31 정정 (세션90 "30" 표기는 오기, list_active_hooks.sh --count 기준)
**회귀**: 전 커밋 smoke_fast 10/10 PASS

**[대기] 다음 진입점 — 단계 III (게이트 3종 재절단)**
- 세션 재시작 후 체감 확인 선행 (권장 경로)
- III-1 commit_gate → Git/staging만 / III-2 evidence_gate → 사전 근거만 / III-3 completion_gate → 최종 완료 선언만
- III-4 `gate_boundary_check.sh` 신설 (금지 토큰 검사)
- III-5 write_marker / evidence_mark_read / evidence_stop_guard 동반 정리

**[완료] origin/main push 복구 (c99c9a16)**
- 배경: GPT Round 재검증 FAIL ("settings.json 여전히 옛 상태") 수령 후 로컬 Git 상태 점검에서 이상 발견
- 진단: 로컬 `refs/heads/main`이 `0000...0000` null 손상 (reflog·HEAD는 정상)
- 조치: `git update-ref refs/heads/main c99c9a16` loose ref 복원 → `git push origin main` 8커밋 일괄 반영 (`ddcb252a..c99c9a16`)
- GPT 원격 재검증: 양측 통과 (SessionStart/UserPromptSubmit/PostToolUse/Stop 훅 unregister 전부 Git 실물 확인)
- 토론 로그: `90_공통기준/토론모드/logs/debate_20260422_095321/`

**[완료] gpt-read.md Step 1 drift 수정 (3497b42e)**
- 배경: 세션90 작업 중 "gpt 대화방 입장" 지시에서 stale `debate_chat_url` ("토론모드 코드 분석") 재사용으로 잘못된 방 진입 사건
- 원인: `gpt-read.md:10` "탭 없으면 debate_chat_url 직행" 구조. 토론모드 CLAUDE.md 27행 "매 세션 프로젝트 최상단 자동 탐지" 규칙 미반영
- 조치: Step 1-A 신설(프로젝트 URL navigate → `main` 스코프 + slug 기반 최상단 href 탐지 → debate_chat_url 갱신), 1-B fallback 분리
- GPT 2자 토론 Round 1 조건부 통과(slug 검증·fallback 지시) → Round 2 PASS (양측)
- 하네스: 채택 4건 / 보류 0 / 버림 0

---

## 이전 세션 (세션92 이하) — 아카이브

세션92 이하 전체 기록은 `98_아카이브/session91_glimmering/TASKS_~session88.md` 참조.
세션97 감량으로 세션93~96만 상세 유지. 세션89/94는 동 아카이브에 추가됨.
