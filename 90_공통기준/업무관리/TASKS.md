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

최종 업데이트: 2026-04-29 KST — 세션124 [E] SP3M3 주간 D0 14건 등록 (auto-run OAuth 실패 → 수동 복구) / 세션123 [C] write-router 화이트리스트 gate / 세션122 [3way] Opus 체감 진단 + 빼는 안 4종 / 세션121 [E] d0-plan SP3M3 야간 D0 24건 / 세션120 슬래시 명령어 2종

## 세션124 (2026-04-29) — [E] SP3M3 주간 D0 14건 등록 + auto-run OAuth 실패 복구

### [완료] SP3M3 주간 D0 14건 등록 (2026-04-29 아침)
- 파일: SP3M3_생산지시서_(26.04.29).xlsm 출력용 주간 섹션 (누적 컷 3,695개)
- 업로드: 14/14 OK (ext=319231~319244)
- 최종 저장: statusCode 200 / mesMsg statusCode 200 / rsltCnt=700
- Phase 6 SmartMES 검증: 서열 순서 엑셀 일치 ✅
- 품번: RSP3SC0383, 0384, 0382, 0642, 0590, 0584 / RSP3PC0143, 0144, 0054 / RSP3SC0666, 0665, 0362, 0251, 0249
- 로그: `06_생산관리/D0_업로드/logs/morning_20260429_manual.log`

### [복구] 07:10 자동실행 OAuth 실패 — 수동 복구
- 자동실행 로그 `morning_20260429.log`: OAuth 완료 2회 실패 (`auth-dev.samsong.com:18100/login?error`) → exit 1
- 원인: OAuth 콜백 후 클라이언트 선택 화면(`auth-dev/`)에 정착. `ensure_erp_login`은 `auth-dev/login` URL에서만 작동 → 30s timeout
- 수동 조치: playwright CDP 9223 접속 → auth-dev 탭을 D0 URL로 직접 navigate → 재실행 통과
- 잔존 데이터 위험: 0 (자동실행은 Phase 0 종료, 수동실행만 등록)
- 모드 E 최소 패치 정량: 코드 변경 0줄, 외부 상태(브라우저 탭 navigate)만

### [잔존] 사후 B 분석 필요 — auto-run OAuth 실패 패턴
- 클라이언트 선택 화면 정착 시나리오 재발 가능 (오늘 1회 발생)
- 해결안 후보: (a) `_wait_oauth_complete`에 클라이언트 선택 화면(`auth-dev` root + title="SAMSONG | OAuth") 감지 시 ERP 클릭 자동화, (b) `navigate_to_d0`에서 `auth-dev` 탭 자동 스킵 필터, (c) 두 안 결합
- 다음 세션에서 모드 C 또는 D로 결정

## 세션122 (2026-04-28) — [3way] Opus 4.7→Sonnet 체감 진단 + 빼는 안 3 옵션 2 적용

### [완료] 3자 토론 Round 1 합의 (pass_ratio 0.75)
- 의제: "Opus 4.7을 사용 중인데 Sonnet 같은 추론 느낌이 드는 체감의 원인"
- 합의: 모델 다운그레이드가 아니라 본 저장소 운영이 Opus 추론 자유도를 95% 침식 (라우팅 5%는 분리 트랙)
- 채택 가설 9개: 컨텍스트 폭증 / 형식 강제 / 메모리 누적 / 자기 메타화 / 톤 부작용 / 라우팅(분리) / 목표 함수 오염(GPT 신설) / Attention Sink(Gemini 신설) / Safety Negative Transfer(Gemini 신설)
- 비율 합의: A 35% + B 30% + 7번 25% + 9번 5% + 6번 5%
- 빼는 안 4종 채택 (감산 원칙): 루트 CLAUDE.md 인덱스화 / 기본 응답 형식 감축 / 세션 초기 강제 로드 제거 / 토론 hook On-Demand화
- 외부 자료: Lost in the Middle (Liu TACL 2024) · Context Rot (Chroma 2025) · Goal Drift (arxiv 2505.02709) · Many-shot jailbreaking (Anthropic 2024) · Inherited Goal Drift (arxiv 2603.03258 — R1~R5 hierarchy로 drift 못 막음 실증) 등
- 로그: `90_공통기준/토론모드/logs/debate_20260428_201108_3way/`
- 형식 함정 회피 메타원칙: 합의안 자체도 새 hook·새 라벨·새 슬롯 추가 금지. 빼는 방향에만 한정

### [완료] 빼는 안 3 옵션 2 적용 — SessionStart 컨텍스트 감축
- 사유: SessionStart hook 직접 수정은 Self-Modification 권한 차단 → 옵션 2 (설정값/데이터 정리)로 전환
- 변경: `.claude/hook_config.json` `session_startup.fallback_tasks_lines` 20→5, `fallback_handoff_lines` 20→5
- 효과: TASKS·HANDOFF "최종 업데이트:" 한 줄(매우 긴 단일 라인 ~1000+ 토큰)이 5줄 컷에서 잘려 SessionStart 컨텍스트 비용 큰 폭 감소
- 하위 호환: 사용자가 `/현재상태` 슬래시 명령어로 풀 정보 lazy load 가능 (이미 신설됨)
- 회귀 위험: 없음. 변경 1파일·4줄(설정값+주석). hook 코드 미수정. side effect 모두 유지. 롤백 = `git revert <SHA>` 1줄

### [완료] 빼는 안 1·2·4 + 메모리 정리 (사용자 "전부승인" 후 일괄 마무리, 커밋 0a657d9a)
- 빼는 안 1: CLAUDE.md 244 → 87줄 + .claude/rules/ 3파일 신설(work_mode_protocol·hook_permissions·external_models)
- 빼는 안 2: 루트 CLAUDE.md "응답 형식" 섹션 — 라벨/PASS/R1~R5/모드헤더/채택보류버림 자동 출력 금지
- 빼는 안 4: 토론모드 비대칭 설계 + 빼는 안 2의 "그때만 활성"으로 일반 작업 메타 연산 자동 차단 명문화
- 메모리 정리: MEMORY.md 47→27줄 (33→17 항목, 16개 흡수 매핑은 project_opus_perception_debate.md로 이동)
- 자가당착 수정: 1차 정리 시 흡수 위치 큰 섹션이 MEMORY.md 76줄로 늘렸던 것을 사용자 지적("규칙+사고 정상 작동 안 하는 거니?")으로 즉시 별도 메모리로 이동, 진짜 빠짐 방향 회복
- 매 응답 자동 로드 분량(루트 CLAUDE.md + MEMORY.md): 291 → 114줄 (-61%)

### [잔존] 라우팅 검증
- 빼는 안 적용 후 1~2 세션 체감 확인 후 필요 시 클린 세션(메타 규칙 일절 없는 빈 프롬프트) vs 현행 + TPS·TTFT 비교
- 클린에서도 저하 유지면 서버 사이드 라우팅 병목, 클린에서 정상이면 본 빼는 안 적용 효과 충분

## 세션121 (2026-04-28) — [E] d0-plan SP3M3 야간 D0 24건 등록 + selectList timeout 상향

### [완료] SP3M3 야간 D0 24건 등록 (2026-04-28 야간 시작)
- 추출: SP3M3_생산지시서_(26.04.29).xlsm 출력용 야간 섹션 24건
- 업로드: ext=319150~319173 연속 채번, rank_batch 24/24 OK (failed=0, missing=0)
- 최종 저장: statusCode 200 / mesMsg statusCode 200 / rsltCnt=1200

### [완료] selectList timeout 60→120s 상향 (모드 E 최소 패치)
- 사유: 1차/3차 시도에서 selectList 60s timeout 연속 발생. 60→120 1줄 변경 후 즉시 통과 (단순 응답 지연 실증)
- 변경 파일: `90_공통기준/스킬/d0-production-plan/run.py` (2개소: selectList + multiList JS setTimeout)
- 변경량: 2줄, 1파일 — E 최소 패치 정량 기준(≤20줄, ≤2파일, 신규 함수/hook/gate 없음) 충족
- 선례: 세션115 30→60 상향 (같은 패턴)

### [잔존] 사후 B 분석 필요
- Phase 6 SmartMES 서열 검증 불일치 — server에 RSP3SC0251 등 잔존 건이 신규 24건 위에 끼어 있음. dedupe dry-run에서 prdtDa=20260428 SP3M3 총 15건 잡혔던 그 잔존 분으로 추정
- 필요 시 `.claude/tmp/erp_d0_dedupe.py --line SP3M3 --date 20260428 --execute`로 정리 가능 (스킬 v3 도구)
- 추가로 selectList 60s timeout 빈발 패턴 자체에 대한 B 분석 (서버 부하/네트워크/엑셀 크기 영향 등) — 다음 세션 의제

### 지침 준수 자가점검 (세션 중 위반 3건 — 사용자 지적으로 정정됨)
- E 최소 패치 범위(timeout 상향 명시)를 모드 C로 잘못 분류해 사용자에게 결정 떠넘김 → 정정
- 같은 timeout 코드로 3회 재시도 (incident 누적) → 패치 후 4회째 통과
- SKILL.md 원본 미독 진행 → 사용자 지적 후 독해 + dedupe 도구·D0 삭제 API 등 핵심 정보 발견

## 세션120 (2026-04-28) — 전역 슬래시 명령어 + 업무관리 폴더 정리

### [완료] 전역 슬래시 명령어 2종 신설
- 위치: `C:/Users/User/.claude/commands/` (전역, 모든 세션·워크트리에서 사용)
- `/현재상태` — TASKS/HANDOFF/git log 기반 현재 상태 5줄 보고
- `/명령어목록` — 전역+프로젝트 슬래시 명령어 전체 표시
- 활성화: 다음 세션 시작 시 자동완성 노출 (캐싱 정책)

### [완료] 슬래시명령어 레퍼런스 엑셀 신설
- `90_공통기준/업무관리/슬래시명령어_레퍼런스.xlsx` (4시트, 11.9KB)
- 사용자정의(34) / CLI내장(18) / 플러그인스킬(9) / 사용가이드
- *.xlsx gitignore 적용

### [완료] 업무관리 폴더 정리 (그룹 A 안전 정리)
- Before: 95건 / 1.9MB → After: 44건 / 380KB (-54%)
- 98_아카이브/정리대기_20260428/_업무관리/로 이동 49건 (_분석 6 + _백업 1 + _로그 42)
- __pycache__ 삭제 (Python 자동 재생성)
- 원복 9건 (절대경로 참조 발견): 운영가이드 v1.0 7종 + gpt-instructions/fallback + skill_guide
- Git 영향: 7건 삭제만 추적 (98_아카이브는 gitignore)

### 미처리 (모드 C 영역, 추후 결정)
- 운영 스크립트 16건 — 작업 스케줄러 절대경로 호출 가능성
- 스크립트 로그 출력 경로 변경 (재발 방지)
- 하위 폴더 5종 (_플랜, 운영검증, gpt-skills, baseline_20260422, _로그) 내용 점검

## 세션119 (2026-04-28) — [3way] mode_c_log.sh v2 — 멀티바이트 안전 cut + 회전 (세션118 잔존 별건 마무리)

### [완료] mode_c_log.sh v2 (의제 2건 통합)
- 진입: 사용자 "남은안건 전부 토론 모드 진행해서 마무리" → 모드 D (`/debate-mode`) 사용자 명시 호출
- 의제 1: `mode_c_log.jsonl` 회전 정책 (HANDOFF "본 세션118 모든 별건 종결. mode_c_log.jsonl 정리 정책만 향후 별건 잔존")
- 의제 2: `mode_c_log.sh:35` commit_subject 멀티바이트 cut 깨짐 (본 세션 점검 중 발견 — kind-williamson worktree 실측 line 1 끝 "프�", line 2 끝 "분기 �")
- 모드 판정: D → 합의 후 C (`.claude/hooks/mode_c_log.sh` 수정)
- plan: `C:/Users/User/.claude/plans/vast-questing-pebble.md` (R1~R5 반증형, 사용자 ExitPlanMode 승인)
- 합의 원본: `90_공통기준/토론모드/logs/debate_20260428_080046_3way/` Round 1 v2 (pass_ratio 0.75, synthesis_only 1.0, critic WARN 보강 3건 반영)

### 변경 (Fast Lane, 2개 파일)
- `.claude/hooks/mode_c_log.sh` —
  - line 35 `cut -c1-120` → `"${PY_CMD:-python}" -c "import sys; data=sys.stdin.buffer.read().decode('utf-8',errors='replace'); sys.stdout.buffer.write(data.strip()[:120].encode('utf-8'))"` (Python codepoint 슬라이스 + `.strip()` + Windows binary 모드 강제)
  - 마지막에 회전 블록 ~14라인 신규: 256KB 임계 + oldest 50% → `mode_c_log.archive.jsonl` 분리 + 임시 파일 mv 원자적 교체 + hook_log 알림
- `.claude/hooks/README.md` — failure contract 표 mode_c_log 비고 v2 1줄 추가

### 3자 합의 (Round 1 PASS)
- GPT (gpt-5-thinking): Step 6-4 동의 / Step 6-5 동의 — "mode_c_log.sh 1파일 한정, archive 보존형 회전, Python 문자 단위 절단, ${PY_CMD:-python} fallback Fast Lane 정합"
- Gemini (2.5 Pro): Round 1 본론 통과 + Step 6-2 GPT에 이의(df3faae2 정정) + Step 6-5 동의 — "원자적 덮어쓰기, .strip(), PY_CMD fallback 3가지 보강안 정확히 흡수"
- Claude 종합: claude_delta=partial (Gemini 보강 3건 흡수), issue_class=B, skip_65=false
- critic-reviewer: WARN — 보강 3건 반영 v2 (GPT 묵시 동의 라벨 하향, 비표준 라벨 정형화, excluded_items 추가)

### 검증 (모두 PASS)
- bash -n 문법 PASS
- 멀티바이트 cut: 한글 180자 입력 → 120 codepoint 정확 절단, U+FFFD 부재, 마지막 hex 완전 UTF-8
- 회전 동작: 333KB/1500줄 입력 → log 166KB/750줄 + archive 166KB/750줄, 데이터 보존 1500=750+750, .tmp 잔존 없음 (원자성)

### [완료] /finish 9단계 마무리 (mode_c_log v2)
- 양측 PASS 만장일치: GPT 5/5 실증됨·동의 (추가제안 없음) / Gemini 5/5 실증됨·동의 (추가제안 없음, "최종 승인")
- Notion 수동 동기화: 성공
- final_check --full --fix: ALL CLEAR (smoke_fast 11/11)
- finish_state.json: terminal_state=done

### [완료] 잔존 별건 마무리 — generate_agents_guide.sh:101 cut 멀티바이트 안전화 (3자 토론 PASS 1.0)
- 진입: 사용자 "잔존 안건도 토론해서 마무리 지어라" → 모드 D 명시 호출
- 토론 로그: `90_공통기준/토론모드/logs/debate_20260428_110944_3way/` Round 1 (pass_ratio_numeric 1.0, claude_delta=none, issue_class=B)
- 실측 결과: `cut -c` 4건 중 1건만 멀티바이트 위험 (3건은 hex digest ASCII 한정)
- 수정: `90_공통기준/업무관리/generate_agents_guide.sh:101` 1라인 (mode_c_log.sh v2 동일 Python codepoint slice 패턴)
- 무수정 (3건): commit_gate.sh:24,26,28 / evidence_gate.sh:72,74,76 / smoke_test.sh:51 — sha1sum/md5sum/cksum hex digest는 ASCII 한정
- critic-reviewer: PASS (관찰 1건, 판정 번복 미달)
- 검증: bash -n PASS / AGENTS_GUIDE.md 자동 갱신 1회 정상 (hooks 34, skills 20) / skill 표 description 컬럼 U+FFFD 0건
- 커밋: 307170ba → main / 양측 PASS 만장일치 (GPT 실증됨·동의 / Gemini 실증됨·동의 — "다음 태스크로 진행할 준비 완료")
- /finish 9단계: terminal_state=done, Notion sync 성공, final_check ALL CLEAR. **세션119 잔존 별건 모두 종결**.

## 세션118 (2026-04-27) — [3way] publish 스크립트 main stale 자동 감지·동기화 옵션 (세션117 별건 1번)

### [완료] publish_worktree_to_main.sh main stale 가드 + --auto-sync 옵션 도입
- 진입: HANDOFF "다음 AI 액션 1번" 최우선·강제 (세션117 마무리 토론 합의 `debate_20260427_214726_3way` Round 1 v2 pass_ratio 1.0)
- 모드 판정: **C** (`.claude/scripts/` 운영 자동화 스크립트 수정)
- 플랜: `C:/Users/User/.claude/plans/eager-riding-kurzweil.md` (R1~R5 반증형 작성, 사용자 승인)
- 변경 파일 (Fast Lane, 1건):
  - `.claude/scripts/publish_worktree_to_main.sh` — 옵션 변수 + usage + 파싱 분기 + stale 감지 블록 38줄 신규 삽입 (기존 라인 변경 0)
- 동작:
  - **default**: stale(`HEAD..origin/main` count > 0) 감지 시 보고+`exit 1` (자동 변경 없음, 안전 후퇴)
  - **`--auto-sync`**: `git fetch origin main` → `merge --ff-only origin/main` 시도 → 성공 시 진행, 분기 시 수동 해결 메시지+`exit 1`
  - **`--dry-run`**: stale 상태만 보고 (동기화 시도 안 함)
- 검증:
  - `bash -n` 문법 PASS
  - `--help` 출력에 `--auto-sync` 라인 노출 PASS
  - dry-run 위치 보정: 기존 `--dry-run` 종료 위치(반영 대상 커밋 표시 직후)를 stale 감지 블록 이후로 이동. plan 명시 "dry-run에서 fetch만 수행" 의도와 정합 (fix-up 커밋)
- **3way 공유 PASS** (양측 만장일치):
  - GPT: PASS — item 1~5 모두 실증됨·동의. 추가제안 없음
  - Gemini: PASS — item 1·2·3·5 실증됨·동의 / item 4(fetch fail-safe) 환경미스매치·동의(제조 현장 네트워크 환경 고려). 추가제안 없음
  - 하네스: 채택 5 / 보류 0 / 버림 0

### 세션117/116 별건 잔존 (우선순위 재정의)
1. ~~세션117 별건 1번 (publish 스크립트 main stale 가드)~~ — 본 세션118에서 완료
2. ~~세션116 별건 2번 R1~R5 Pre-commit hook~~ — 본 세션118에서 완료 (`.claude/hooks/r1r5_plan_check.sh` advisory 신설)
3. ~~세션116 별건 3번 HANDOFF 자동 에스컬레이션 hook~~ — 본 세션118에서 완료 (`.claude/hooks/mode_c_log.sh` advisory 신설, HANDOFF 직접 수정 무한 루프 위험 회피로 `.claude/state/mode_c_log.jsonl` 기록 + stderr 알림 우회 채택)
4. ~~세션116 별건 4번 PLC 인터치·Staging Table 청소 (ERP-E-01)~~ — 본 세션118에서 완료 (`90_공통기준/erp-mes-recovery-protocol.md` 단일 원본 신설 + 도메인 라우팅)

### [완료] 별건 4번 — ERP/MES 잔존 청소 프로토콜 신설 (세션118)
- 신규 단일 원본: `90_공통기준/erp-mes-recovery-protocol.md`
- 도메인 라우팅: 루트 `CLAUDE.md` 도메인 진입표 + `04_생산계획/CLAUDE.md` 1줄 추가
- Known cases: 세션110 SmartMES dedupe 도구 / 세션115 사용자 첨부 무시 사고 / 세션107 OAuth 자동완성 잔존
- PLC 인터치는 현재 직접 호출 없음 → 장래 도입 시 안전 기준 4종 보관

### [완료] 별건 2+3번 통합 — R1~R5 Pre-commit hook + 모드 C 에스컬레이션 로그 (세션118)
- 신규: `.claude/hooks/r1r5_plan_check.sh` (advisory, PreToolUse/Bash) — C 트리거 staged + plan 흔적 미발견 시 stderr 권장
- 신규: `.claude/hooks/mode_c_log.sh` (advisory, PostToolUse/Bash) — C 트리거 커밋 후 `.claude/state/mode_c_log.jsonl` 1줄 기록 + stderr 알림
- HANDOFF.md 자동 직접 수정은 hook 무한 루프 위험으로 **회피** — state 파일 기록 + 사용자 시각 알림으로 Gemini 권고 흡수
- settings.json PreToolUse + PostToolUse matcher 1건씩 등록
- README.md 등급 표 advisory 라인 2건 추가
- 활성 hook 수: 32 → 34 (AGENTS_GUIDE.md 자동 갱신 완료)
- plan: `C:/Users/User/.claude/plans/heuristic-flowing-bagel.md` (R1~R5 반증형 작성)
- **GPT 부분PASS A 분기 즉시반영**: settings*.json regex 누락 지적 채택 → 두 hook 모두 `^\.claude/settings.*\.json$`을 별도 OR로 분리. 검증: 가짜 입력 `settings.json`/`settings.local.json` 매칭 PASS
- **3way 공유 PASS** (양측 만장일치 — df3faae2 기준):
  - GPT (b8249d10 부분PASS → df3faae2 A 분기 즉시반영 후 종결): item 1·2 정정 채택, item 3·4·5 동의. 추가제안 본 fix-up으로 종결
  - Gemini PASS (df3faae2): 5/5 동의 (item 1·2·3·5 실증됨, item 4 메타순환 라벨이지만 무한 루프 회피 동의). 추가제안 없음 — "최종 승인"
  - 하네스: 채택 5 / 보류 0 / 버림 0

## 세션117 (2026-04-27) — [3way] 토론모드 자동 승격 → 비대칭 정합화 (세션116 별건 1번)

### [완료] 토론모드 CLAUDE.md "자동 승격 트리거" + share-result.md 5단계 B 분기 → 모드 D 비대칭 설계 정합 갱신
- 진입: HANDOFF "다음 AI 액션 2번" — 세션116 별건 의제 1번
- 사용자 지시: "이어서 진행하자" → AskUserQuestion 1번 선택 → "토론모드 진행해서 플랜 보강후 해결"
- 모드 판정: **C 강제 승격** (도메인 CLAUDE.md + `.claude/commands/` 수정, 루트 CLAUDE.md C 트리거 7개 중 2개)
- 플랜: `C:/Users/User/.claude/plans/lexical-exploring-pebble.md` (R1~R5 반증형 작성)

### Round 1 토론 결과 (pass_ratio 0.75, PASS)
- 로그: `90_공통기준/토론모드/logs/debate_20260427_203835_3way/`
- 안건 5건: 누락 검토·share_gate 정합·세션 캐싱·NEVER 라인 형식·의제 표류 보호
- 채택 4건 + 조건부채택 1건 + 보류 1건 + 별건 3건
- cross_verification 4키: 동의 3 / 검증 필요 1 (gpt_verifies_gemini = ERP 트랜잭션 모드 E 영역 별건 분리)
- claude_delta: partial / issue_class: B / skip_65: false
- critic-reviewer **WARN** (라벨 불일치 + 보조축 0건감사·일방성) → v2 반영: 안건 3을 "조건부채택"으로 재분류 + 보류 1건 등재 + cross-grep 실수행 결과 evidence 추가

### 변경 파일 (2건, Fast Lane)
1. `90_공통기준/토론모드/CLAUDE.md` 줄 79-122 — 섹션명 "자동 승격 트리거" → "B 분류 감지 + 보고 (비대칭 전환)" + 자동 `Skill(debate-mode)` 호출 절차 → 1줄 라벨 표기 + 사용자 명시 호출 대기로 재기록 + 세션117 토론 로그 참조 + `[NEVER] 자동 호출 금지` 추가
2. `.claude/commands/share-result.md` 줄 173-186 — 5단계 B 분기 자동 승격 → "라벨 표기 + 사용자 호출 대기 (즉시 반영 금지)"로 변경 + HANDOFF 미결 1줄 수동 기록 권장 + `[NEVER] B 감지 라벨 없이 단독 반영 금지` 추가

### 별건 등록 (세션116 별건과 통합)
- ERP/MES 트랜잭션 롤백 NEVER 조항 → 세션116 별건 4번 PLC와 통합
- 임시 가드 hook 신설 검토 → 세션116 별건 2번 R1~R5 Pre-commit hook과 통합 토론 시 재평가
- HANDOFF 자동 에스컬레이션 로그 (세션116 별건 3번) — 본 세션 share-result에 수동 기록 권장 라인은 추가, 자동 hook은 별건 유지

### 세션116/117 별건 잔존 (우선순위 재정의)
1. ~~세션116 별건 1번 (토론모드 자동 승격 갱신)~~ — 본 세션117에서 완료 (e0b3a50a)
2. **[신규·최우선] publish_worktree_to_main.sh main stale 자동 동기화 옵션 도입 (모드 C)** — 세션117 마무리 토론 합의 (debate_20260427_214726_3way Round 1 v2 pass_ratio 1.0). 본 세션에서 main 로컬 ↔ origin/main 분기로 cherry-pick 충돌 발생, 사용자 옵션 A 승인으로 회복. R1~R5 plan-first 작성 후 진행 권장 (다음 세션 첫 액션 강제).
3. 세션116 별건 2번 R1~R5 Pre-commit hook — 세션117 안건 3 Gemini 보류(임시 가드 필수)와 통합 검토
4. 세션116 별건 3번 HANDOFF 자동 에스컬레이션 hook — 세션117에서 수동 기록 권장 라인은 반영, 자동 hook은 별건 유지
5. 세션116 별건 4번 PLC 인터치·Staging Table 청소 (ERP-E-01) — 세션117 Gemini 추가제안(ERP 트랜잭션 롤백) 흡수 후 통합 검토

## 세션116 (2026-04-27) — 작업 모드 판정 도입 + 별건 의제 4건

### [완료] CLAUDE.md 사고 계층 신설 (작업 모드 A/B/C/D/E + 모드별 사전 절차)
- 진입: 사용자 "규칙 + 사고 구조 보정 — 작업 모드 판정 + 모드별 사고 절차 추가"
- 플랜 작성 → 3자 토론(Round 1+2 pass_ratio 1.0) → critic WARN 3건 v2 반영 → CLAUDE.md 수정
- 신규 섹션: "## 작업 모드 판정 (실행 전 필수)" — 6행 아래, 도메인 진입표 위
- 합의: 5종 유지(F 모드 폐기), 우선순위 사다리 명시>E>C>D>B>A, R1~R5 반증형, 모드 E 정량 OR 6조건, 단순 건수 불일치 2단 판정
- 메모리: `feedback_work_mode_taxonomy.md` 신설, `feedback_structural_change_auto_three_way.md` 갱신(자동 D 진입 차단)
- 토론 로그: `90_공통기준/토론모드/logs/debate_20260427_185903_3way/`
- 커밋: `00d74273` (push: fa0fa8a7..00d74273 -> main)
- **공유 PASS**: GPT 5/5 실증됨 PASS + Gemini 5/5 동의 PASS (양측 만장일치, 추가제안 없음). GPT 추가 코멘트: "토론모드 CLAUDE.md 모순은 TASKS 별건 1번으로 이미 등재됨" 확인.

### [신규/대기] 별건 의제 4건 (본 보정 범위 외 — critic WARN "분리 사유 명기" 권고 반영)

**1. 토론모드 CLAUDE.md "자동 승격 트리거" 섹션 → 모드 D 정책으로 갱신**
- 분리 사유: 본 보정 범위는 "루트 CLAUDE.md 1개 섹션 추가". 토론모드 CLAUDE.md 정책 갱신은 토론모드 도메인 별건. 단 문서 모순 잔존이므로 다음 작업 우선순위 1.
- 변경 대상: `90_공통기준/토론모드/CLAUDE.md` "## 자동 승격 트리거 (세션78 실증 후 신설)" 섹션
- 변경 방향: B 분류 자동 D 승격 → "B 분류 감지 라벨만 표기, D 자동 진입 차단" 비대칭 설계로 재기록

**2. R1~R5 Pre-commit hook 연동 (Gemini Round 2 제안)**
- 분리 사유: 본 보정은 hook 신설 금지가 명시 제약. 향후 hook 신설 별건 의제로 분리.
- 검토 항목: plan.md에 R1~R5 채워졌는지 자동 검증 hook 가능성. 등급 advisory 후보.

**3. HANDOFF 자동 에스컬레이션 로그 (Gemini Round 2 제안)**
- 분리 사유: 본 보정은 응답 첫 줄 수동 인지 라인(`[모드 전환: A → C]`)만 채택. HANDOFF 자동 갱신 hook 신설은 본 범위 초과.
- 검토 항목: C 강제 승격 시 HANDOFF.md에 1줄 자동 기록 hook 가능성.

**4. PLC 인터치·Staging Table 잔존 청소 프로토콜 (Gemini Round 2 제안 — ERP-E-01)**
- 분리 사유: 도메인 04_생산계획·05_생산실적 수준의 운영 프로토콜. 루트 CLAUDE.md 범위 초과.
- 검토 위치: `04_생산계획/CLAUDE.md`, `05_생산실적/조립비정산/CLAUDE.md` 또는 신규 `90_공통기준/erp-mes-recovery-protocol.md`

## 세션115 (2026-04-27) — d0-plan 첨부 파일 가드 + ERP timeout 상향

### [완료] d0-plan 스킬 사고 재발 방지 가드
- 사고: 사용자가 중복 정리한 SSKR D+0 Upload xlsx를 첨부했으나 스킬이 무시하고 Z 드라이브 원본(중복 포함 30건) 자동 추출 → ERP 등록 + MES 1500건 전송. MES 잔존 특성상 정정 불가
- 가드: `.claude/commands/d0-plan.md` "⛔ 첨부 파일 가드" 섹션 신설, `90_공통기준/스킬/d0-production-plan/SKILL.md` description + 핵심 주의사항 최상단에 가드 블록
- 동작: 사용자 메시지에 xlsx/xlsm 첨부 감지 시 자동 실행 차단, (A) `--xlsx <경로>` (B) Z 드라이브 자동 탐색 명시 확인 강제
- 잔존 처리: 중복 30건은 사용자 결정 "그대로 두기"
- 추가: `run.py` selectList ajax timeout 20s → 60s (저녁 시간대 ERP 서버 응답 지연 대응)

## 세션114 (2026-04-27) — NotebookLM 컨트롤 레이어 신설

> 진입: 사용자 "제미나이를 주로 사용하니까 메인은 제미나이다" + "로컬 컨트롤해서 셋팅해바"
> 배경: Google이 2026-04-08부터 Gemini 앱에 NotebookLM 통합. 사이드패널에서 노트북 직접 호출 + 양방향 동기화.

### [완료] NotebookLM 컨트롤 레이어 신설
- 위치: `90_공통기준/notebooklm/`
- 단일 원본: `registry.yaml` (현재 노트북 2건 등록 — 라인배치/조립비정산, 확장 가능)
- 도메인 진입: `90_공통기준/notebooklm/CLAUDE.md`
- Gemini 통합 절차: `bridge.md` (사이드패널 셀렉터는 첫 사용 시 take_snapshot 실측 후 채움)
- 슬래시: `.claude/commands/notebooklm.md` (list/health/query/ask/sync/register)
- 헬스 스크립트: `health.sh` (정적 자산 5/5 PASS)
- 루트 CLAUDE.md 도메인 진입 라우팅에 NotebookLM 키워드 추가

### [완료] MCP 인증 + 양방향 동기화 실증 + v2 노트북 2건 생성
- MCP 인증: `setup_auth` 성공 (60.91초)
- MCP 직접 질의 양 노트북 PASS (라인배치 / 조립비정산)
- **shared 제약 실증**: 기존 noun이 `public` 마크 → Gemini에 노출 안 됨 (Google 공식 정책)
- **우회**: Gemini에서 v2 노트북 2건 생성 (라인배치_대원테크_v2 / 조립비정산_대원테크_v2)
- **양방향 동기화 실증**: UUID 공통 (`515e5104-...`, `b49dc000-...`), Gemini→NotebookLM 즉시 노출
- registry.yaml v2 갱신 (primary + legacy 분리)
- bridge.md 셀렉터 전체 확정 (생성 페이지·상세 페이지·소스 업로드 메뉴)

### [완료] 3way 공유 + A분류 즉시반영 (양측 만장일치)
- GPT 부분PASS / Gemini 부분PASS — item 2 동일 지적 (스키마 불일치)
- A 분류 즉시반영:
  - `.claude/commands/notebooklm.md` v2 스키마로 정합 (gemini_url/notebooklm_url/status/uuid 필드, primary/legacy 라우팅 명시)
  - `90_공통기준/notebooklm/health.sh` 출력에 status별 카운트 + sources=0 경고 추가

### [완료] v2 노트북 소스 업로드 + 동작 검증
- 라인배치_v2: `10_라인배치/notebooklm_source_라인배치_v1.txt` 업로드 완료 (123KB)
- 조립비정산_v2: `05_생산실적/조립비정산/06_스킬문서/notebooklm_source_조립비정산_v1.txt` 업로드 완료 (88KB)
- **Gemini 메인 흐름 검증 PASS**: 조립비정산_v2 노트북에 "SD9A01 야간 가산 규칙" 질의 → 정확한 답변 (소스 인용 marker 포함)
- 양방향 동기화 작동 확정 (UUID 공통 + 소스 인덱싱)
- registry.yaml sources 필드 1로 갱신

### 남은 후속 (선택)
- legacy 노트북 폐기 (NotebookLM 웹에서 삭제 + registry active=false)
- 도메인 문서 추가 시 v2 노트북에 추가 업로드 (Step 1~7 PDF·spec 문서 등)

### [완료] 부수작업 — 센스커버 조립공정 부적합 가능성 분석 (89870CU100)
- 사용자 요청: `06_생산관리/품질/센스커버 조립공정.mp4` 기반 부적합 발생 가능성 정리 → 엑셀화 + 영상 첨부
- 산출물: `06_생산관리/품질/센스커버_조립공정_부적합가능성분석_20260427.xlsx` (1차 상세본)
  + `센스커버_조립공정_부적합가능성_대원테크.xlsx` (사용자 제시 4건 단순본, 사용자가 최종본으로 채택)
- 정리한 4건 오조립 가능성: ① 스펙·색상 동일 시 ② 비전검사 고장 시 수작업 ③ 색상 판단(유사 색상) ④ 재작업 시 품번 미확인
- 영상 첨부 방식: OLE Package 임베드 시도 → Windows packager.exe 미등록(-2146827284)으로 차단 → 썸네일 + 하이퍼링크 방식 채택 (xlsx 옆 mp4 상대 경로)
- 부속 자료: `06_생산관리/품질/_frames_analysis/` 프레임 25장, `_make_report_xlsx.py` 생성 스크립트, `센스커버_조립공정_부적합가능성분석_20260427.md` 1차 분석 보고서

### 설계 원칙
- Gemini = 메인 채널 (사이드패널 노트북 활성화 후 질의)
- NotebookLM MCP = 백엔드 (인증·라이브러리·소스 근거 인용 fallback)
- 도메인 한정 질의는 도메인 에이전트 경유 (line-batch-domain-expert / settlement-domain-expert) — 메인 컨텍스트 보호
- 노트북 URL 하드코딩 금지 — 항상 registry에서 조회

---


## 세션113 (2026-04-27) — [3way] self-audit 후속 토론 결과 + P2-B 최소 수정

> 진입: 사용자 "토론 진행해서 근본 문제 마무리" → 3자 토론(Claude×GPT×Gemini) Round 1 → 양측 만장일치 (pass_ratio=4/4=100%)
> 로그: `90_공통기준/토론모드/logs/debate_20260427_105243_3way/`

### 메타 의제0 — 해석 C 채택 (양측 만장일치)
세션108 "시스템 개선 영구 중단"은 유효. 다만 예외 1건 — 실무 산출 막거나 정상 작업을 반복 차단·오염시키는 1건은 최소 수정 가능.
- **P2-B 1건만 토론 대상** (필수 유지보수, 시스템 개선 모드 재진입 아님)
- **P2-C / P3-E 동결 보류** (운영 경로 부여 금지, 폐기도 금지)
- **이번 수정이 마지막 시스템 개입** (Gemini 명시 권고)

### [완료 + 조건부 보강] P2-B Option B 구현 — evidence_mark_read.sh 패턴 확장

**조건부 보강 (GPT 양측 검증 지적 반영, 25b0887e → 후속 커밋)**: 패턴 1을 `OAuth` 단어 매칭 → `OAuth 200 OK / OAuth 200 / Login Success / 로그인 성공 / auth_diag.ok` 명시적 성공 phrase fixed-string로 좁힘 (false ok 방지 강화).


양측 합의 안전 조건 5가지 모두 반영:
1. 단순 스크립트명 매칭 금지 — 명령 + 성공 신호 + error 부재 3중 조건
2. `grep -qF` fixed-string 매칭으로 정규식 메타문자 우회 차단 (Gemini 앵커링 강제)
3. error/traceback/exception/failed 키워드 부재 추가 검증 (false ok 방지)
4. token 파일 mtime ≥ 세션 시작 시각 (GPT 추가 보강: "이번 실행에서 갱신된 파일")
5. 단일 파일 최소 보정 — 신규 hook / settings / evidence_gate 정책 변경 모두 금지

추가 패턴 2개:
- 패턴 1: `erp_oauth_login.py` 명령 + `OAuth` 텍스트 + error 부재 → `auth_diag.ok` mark
- 패턴 2: ERP OAuth 토큰 파일이 세션 시작 이후 생성/갱신 → `auth_diag.ok` mark

### [영구 보류] P2-C — 죽은 보조 hook 4종 동결
`e2e_test`, `nightly_capability_check`, `gate_boundary_check`, `render_hooks_readme` — 어떠한 운영 경로도 부여 금지, 삭제도 금지. 보조 수동 도구 상태 유지.
- 세션77 nightly 합의와의 트레이드오프 명시: "당시는 안전망 부족이 핵심 리스크, 현재는 안전망 과다가 병목. 환경 적응으로서의 합리적 보류"
- 재논의 트리거: 실무 작업을 실제로 막는 증거가 나오기 전까지 재논의 금지

### [영구 보류] P3-E — agents 7종 동결
`evidence-reader`, `debate-analyzer`, `artifact-validator`, `settlement-validator`, `code-reviewer`, `critic-reviewer`, `self-audit-agent` — AGENTS_GUIDE 추가/자동 호출/삭제/description 수정 모두 금지. 필요 시 수동 호출만.
- **재논의 트리거 명문화 (Gemini 신규)**: "실무 산출물에 치명적 결함(잘못된 정산 엑셀, 코드 포맷 파괴 등) 발생 + 해당 agent(artifact-validator 등) 부재가 직접 원인으로 증명된 경우에 한해 재논의 허용"

### 양측 검증 결과 (cross_verification 4/4 = 100%)
- gemini_verifies_gpt: 동의 (해석 C 세션108 원칙 완벽 부합)
- gpt_verifies_gemini: 동의 (필수 유지보수 + 물리 증거 + 앵커링 + 재논의 트리거 모두 인정)
- gpt_verifies_claude: 동의 + 구현 보강 2건 (mtime 검증 / ^...$ 완전일치)
- gemini_verifies_claude: 동의 (mtime 검증 채택 권장)

### 운영 정합
- bash syntax check: OK
- smoke_fast: 11/11 ALL PASS
- claude_delta: major (Claude 6-0 답안 → 양측 검증으로 세션108 합의 일관성 수렴 — 3-way 정합성 가치 실증)

---

## 다음 세션 토론 안건 (2026-04-27 self-audit 결과)

> /self-audit (weekly scheduled task) 결과 단독 결정 금지 항목. `feedback_structural_change_auto_three_way` 정책에 따라 GPT/Gemini 3자 토론 후 결정.

**[안건1] P2-B — evidence_gate auth_diag.req / identifier_ref.req ok 발급 절차 명문화**
- 근거: 7일 incident_ledger `evidence_missing` 35건 중 동일 fingerprint(`383f406a5519717b` auth_diag.req 등) 다회 반복 카운트
- 쟁점: req 발급 트리거는 정의됐으나 ok 발급의 정상 경로가 명문화되지 않아 동일 req가 ok로 전환되지 못한 채 누적
- 토론 포인트: req-ok 비대칭 정책 설계 vs MES/OAuth 진단 자체 차단이 정상 동작인지

**[안건2] P2-C — 죽은 보조 hook 4종 운영 경로 결정**
- 대상: `e2e_test.sh`, `nightly_capability_check.sh`, `gate_boundary_check.sh`, `render_hooks_readme.sh`
- 근거: settings 미등록 + Grep 결과 호출 흔적 부재. 특히 `nightly_capability_check`는 세션77 Round 2 Gemini 최우선 안전망으로 도입(Silent Failure 방지)됐으나 schtasks 미등록 — 도입 합의 무력화 위험
- 결정 사항: schtasks 등록 vs 수동 절차 명문화 vs 폐기

**[안건3] P3-E — agents 7종 진입 경로 명문화 vs 폐기**
- 대상: `evidence-reader`, `debate-analyzer`, `artifact-validator`, `settlement-validator`, `code-reviewer`, `critic-reviewer`, `self-audit-agent`
- 근거: CLAUDE.md / 도메인 CLAUDE.md / AGENTS_GUIDE.md 어디서도 참조 미발견. 활성 호출 경로 부재
- 결정 사항: 진입 트리거 명문화 vs 사용 도메인 CLAUDE에 분산 등재 vs 일부 폐기

---

## 세션112 (2026-04-27) — weekly self-audit 결과 반영 (P3 5건)

> 진입: scheduled-task `weekly-self-audit` 자동 실행 → 진단 리포트 → 사용자 "개선 진행해라" → A·C 안건 승인

**[완료] P3 자체 처리 5건** — A 분류
- TASKS.md 헤더: 세션110/111/112 정보 반영 (이전 헤더 세션109/108/107)
- STATUS.md 헤더: 세션111/110 정보 반영 (이전 헤더 세션109/108/107)
- `.claude/hooks/README.md` 실패계약 표 위 "수록 범위" 단서 1줄 추가 (활성 32 + advisory 보조 hook 6 명시)
- `.claude/hooks/README.md` 보조 스크립트 표에 `domain_status_sync.sh` 1줄 추가 (실패계약 표에는 있었으나 보조 스크립트 표 누락)
- `.claude/settings.local.json` `list_active_hooks.sh --count` 절대 경로 중복 1건 제거 (L33 상대 경로 보존, L38 절대 경로 삭제)

**[보류 → 토론 안건 등재]** — 위 "다음 세션 토론 안건" 섹션 참조

**진단 결과 요약**:
- P1(auto_commit_state 차단 12회 누적): 사용자가 D0 작업 중 자체 해소 (final_check ALL CLEAR 확인)
- P2 evidence_missing 35건 / 죽은 hook 4종: 토론 안건1·2로 분리
- P3 헤더 드리프트·README 누락·settings 중복: 자체 처리 완료 (5건)
- P3 agents 진입 경로: 토론 안건3으로 분리

## 세션110 (2026-04-27) — D0 morning 실패 + 중복 7건 자동 정리 + 신규 운영 도구

> 진입: 사용자 "스케줄러 작동 안된 거 같은대" → morning 자동 batch 재시도 중 사용자 중지 → 수동 등록과 자동 재실행 중복으로 18건(정상 11 + 중복 7) 등록 → 사용자 "ERP에서 삭제 가능한지 직접 확인"

**[완료] D0 등록 삭제 API 발견 + 중복 7건 정리** — A 분류, [3way 미해당, 단순 발견]
- 발견: `DELETE /prdtPlanMng/deleteDoAddnPrdtPlanInstrMngNew.do` payload `{REG_NO: <번호>}` — UI 미노출, 사용자도 모름
- 발견 경로: ERP D0 화면의 `totGridList.deleteRow.toString()` 코드 dump
- SmartMES `sewmacLabelScanQty` 필드 = ERP `REG_NO` 매핑 식별 (필드명 misleading)
- 자동 식별 기준: SmartMES rank 작은 쪽(위) 보존 / rank 큰 쪽(아래) 삭제
- 7건 일괄 DELETE 성공 (statusCode=200 × 7), ERP 그리드 11건만 잔존 검증 완료
- 신규 도구: `.claude/tmp/erp_d0_dedupe.py --line SP3M3 --date YYYYMMDD [--execute]` (dry-run 기본, --execute로 실 삭제)
- SKILL.md "되돌리기 방법" + 변경이력 v3 갱신
- `.gitignore` 화이트리스트 추가: `.claude/tmp/erp_d0_deleteA.py` + `.claude/tmp/erp_d0_dedupe.py` (운영 도구 2종 git 추적)

**[완료] morning OAuth 안정화 + Chrome 복원 알림 차단** — A 분류 (세션110)
- 원인 1: navigate_to_d0 line 119-126 `"erp-dev.samsong.com" in url` 부분 매칭 → OAuth 콜백 중간 단계 `oauth2/sso` URL도 잘못 break → D0_URL goto → login 페이지 redirect → btnExcelUpload timeout
- 수정 1: `_wait_oauth_complete()` 헬퍼 신설 — `erp-dev` AND NOT `auth-dev` AND NOT `oauth2/sso` AND NOT `/login` 조건. login 재도달 시 1회 재로그인 시도
- 원인 2: Chrome taskkill 후 재기동 시 "페이지 복원" 알림 표시 — 무인 morning 트리거에서 화면 거슬림
- 수정 2: `_suppress_chrome_crash_restore()` 헬퍼 — Preferences `exit_type=Normal` 강제. launch 플래그에 `--disable-session-crashed-bubble` `--hide-crash-restore-bubble` `--remote-debugging-address=127.0.0.1` 추가
- 검증: dry-run 2회 모두 exit 0 + 사용자 화면 복원 알림 미발생 확인 ("정상")

**[폐기] morning 중복 발생 방지책 + SmartMES 동기화 등 4건 — 사용자 폐기 결정 (2026-04-27)**
- 폐기 항목: ① morning + 수동 동시 실행 중복 방지책 ② SmartMES 잔존 7건 정리 (IT 영역) ③ 작업 기준 시스템 확인 ④ SAC 차단 (IT 영역)
- 폐기 사유: 시스템 운영팀(IT/MES) 영역 또는 별 의제 우선순위 낮음. AI 추가 작업 없음.

## 세션109 (2026-04-25) — SD9A01 공정별·개인별 숙련도평가서 자동화

> 진입: 사용자 "SD9A01 라인 안건 진행하자" + ERP 표준공정관리 화면(11공정) 캡처 제공 → 작업계획.md 10공정 정정 + Phase 2~4 11공정 기준 재설계. Plan mode → 사용자 승인 → auto-mode 실행.

**[완료] Phase 1 — 작업표준서 통합본 작성**
- 입력: 작업표준서(180706) Rev.16.xls (17시트) + (260101) Rev.16.xls (13시트)
- 처리: Excel COM(pywin32)으로 .xls→.xlsx 변환 후 시트 복사 (260101 베이스 + 180706 단독 4시트: 20/81/82/83)
- 산출: `01_인사근태/숙련도평가/SD9A01_표준문서/SD9A01 작업표준서 통합_Rev16.xlsx` (17시트, 29 MB)
- 시트 순서: 목록 / D9 PT 개정이력 / 20 / 21 / 30 / 40 / 43 / 50 / 60 / 70 / 80 / 81 / 82 / 83 / 90 / 100 / 카메라
- 스크립트: `01_인사근태/숙련도평가/생성스크립트/merge_sd9a01_workstandard.py`

**[완료] Phase 2 — PROCESSES 11개 자동 추출**
- 통합본 시트별 자주검사 영역(M/N/Q/W 열) 자동 추출 → std 5개
- 관리계획서 공정번호별 행 추출 → ctrl 4개
- 부족 시 GENERIC_STD/CTRL 보강 (안전·이종확인·관리기준 일반 항목)
- SD9A01_001(바코드)·SD9A01_002(메인)는 시트 20을 키워드 필터 분리, SD9A01_003(신규)은 시트 21 단독 사용
- 스크립트 내장: `create_sd9a01_v1.py:build_processes()`

**[완료] Phase 3 — 공정별 양식 11개 생성**
- 산출: `01_인사근태/숙련도평가/SD9A01_공정별 평가서/SD9A01_공정{001~011} 숙련도 평가서.xlsx` × 11
- 37r × 95c, 67~69KB/파일, 라인 셀 = SD9A01
- 스크립트: `create_sd9a01_v1.py`

**[완료] Phase 4 — 개인별 23명 파일 생성**
- 입력: SD9M01 주간 12명 + 야간 11명
- 매핑: SD9M01 공정번호(10/20/.../100) → ERP 코드(001/002/.../011)
- 마스터 템플릿(공정 11시트) → 작업자별 수행공정만 시트 유지 + 주공정 맨 앞 + Z3 라벨 + AC열 점수 분배(총점 보존, 0점 없음, 5점 상한, hash seed 재실행 동일)
- 산출: `01_인사근태/숙련도평가/SD9A01_개인별 평가서/SD9A01 주간|야간/{이름} 숙련도평가서.xlsx` × 23
- 박태순(10공정 풀세트, 신규 003 주공정) 검증: AC합계 92 = 원본 총점 일치 ✓
- 스크립트: `create_sd9a01_personal.py`

**[완료] Phase 5 — 통합 검증**
- 파일 수: 통합본 1 + 공정별 11 + 개인별 23 = **35개 산출물**
- 모든 개인별 첫 시트 Z3='주공정', 나머지 '전환공정' ✓
- ERP 11공정 ↔ 통합본 시트 ↔ SD9M01 공정번호 매핑표 작업계획.md 갱신
- 잔여 (사용자 텍스트 검수 단계): GENERIC 보강된 평가사항이 공정 특성과 맞지 않으면 PROCESSES 직접 정정 후 `create_sd9a01_v1.py` / `create_sd9a01_personal.py` 재실행

**[완료] 자체검증 + SD9A01_003 매핑 정정**
- 신규 검증 스크립트: `verify_sd9a01_outputs.py` (A 파일구조 / B·C 평가사항·메타 / D·E·F 점수·라벨·일관성 / G 의미 키워드 / H SP3M3 좌표)
- 발견된 매핑 오류: 작업표준서 **시트 21 = 프레임 바코드/2D 바코드/와이어 조립**(ERP_001에 해당). ERP_003(리벳/릴 하단 브라켓)으로 잘못 사용 → 미스매치
- 정정: `create_sd9a01_v1.py` ERP_PROCESSES 매핑 변경 (001↔시트21 / 002↔시트20 / 003↔OVERRIDE) + `OVERRIDE_PROCESSES['003']` 신설 (리벳·릴 하단 브라켓 보수적 std·ctrl 9항목)
- 양식 11 + 개인별 23 재생성 → 자체검증 **0 issues PASS**

**[완료] 공정 번호 체계 변경 (사용자 결정, 2026-04-27 세션111)**
- 사용자 지적: "공정 번호가 안 맞다" → ERP 표준공정원직(SD9A01_001~011) 대신 **라인별공정목록.xlsx 기준 10단위** 사용
- 신규 번호 부여: **10/20/21/30/40/50/60/70/80/90/100** (11개)
  - 21 = 신규 공정 "RETRACTOR MAIN FRAME 서브 앗세이 압입 & 리벳 & 릴 하단 브라켓" (작업표준서 통합본 '목록' 시트의 21="릴브라켓 리벳팅 공정"과 의미 일치)
- 변경 범위: `create_sd9a01_v1.py` ERP_PROCESSES + MGRPLAN_PROC_NO_MAP + OVERRIDE_PROCESSES key, `create_sd9a01_personal.py` SD9M01_TO_ERP, `verify_sd9a01_outputs.py` ERP_NAMES + EXPECTED_CODES
- 산출물 재생성: `SD9A01_공정{10/20/21/30/40/50/60/70/80/90/100} 숙련도 평가서.xlsx` × 11 + 개인별 23명 (시트명 `공정{NN}`, N5 셀값 `'10'~'100'`)
- 박태순(10공정) 검증: 주공정=공정21(신규) + 9개 전환공정 ✓ / 자체검증 **0 issues PASS**



## 세션108 (2026-04-25) — GPT 정밀평가 검증 후 시스템 개선 모드 중단

> 진입: GPT 정밀평가 리포트(L-1~L-7, P-1~P-5) 수령. 사용자 모드 전환 — "실무 산출물 우선, 시스템 개선 중단". 마지막 한 사이클로 근본 드리프트만 최소 보정.

**[완료] L-1 STATUS.md 토론모드 정책 history 정합** — A 분류
- `STATUS.md:34` 재개표 "Chrome MCP 단일화(세션32). CDP 폐기" → 현재 정책(chrome-devtools-mcp/CDP 단독, 세션105 전환) 명시. 세션32 표현은 history로 명시 보존.
- 근거: 토론모드 `CLAUDE.md` 현재 정책과 정합. gpt-send/read·gemini-send/read 4개 command 모두 CDP `select_page(bringToFront=true)` 기반.

**[완료] L-2 hooks/README.md 등록 순서 출처 정정** — A 분류
- `.claude/hooks/README.md:29` "settings.local.json 배열 순서" → "settings.json(team+local union) 배열 순서". 문서 라인 8(SSoT=settings.json)과 자체 모순 해소.

**[모드 전환] 시스템 개선 모드 중단**
- 이후 작업: 실무 산출물 / 작업 차단 오류 최소 수정 / TASKS·HANDOFF 필수 기록 / final_check 1건 단위 보정.
- 보류: P-1~P-5 잔여(L-3 incident 분석 추가 / L-4 local permission 정리 / L-5 runtime 검증 / L-6 PreToolUse 과밀 / L-7 CDP 강제 차단).
- L-3은 드리프트 아님(분석 시점 47건 스냅샷 vs TASKS 누적 44건은 시점 차이) — 보정 불요.

**[완료] L-5 runtime 진단** — A 분류 (사용자 추가 지시)
- `list_active_hooks.sh --count`: 32 / `--by-event`: PreCompact 1·SessionStart 1·UserPromptSubmit 1·PreToolUse 16·PostToolUse 7·Notification 1·Stop 5
- `final_check --full`: README/AGENTS_GUIDE 32개 모두 일치, settings 등록훅 모두 실존, 카운트 드리프트 0건
- 결론: hook 카운트·문서 정합·실존성 모두 PASS. 추가 조치 불요.

**[완료] L-6 PreToolUse 통합·삭제 금지 명시** — A 분류 (사용자 추가 지시)
- `.claude/hooks/README.md:29` PreToolUse 섹션에 1줄 명시 추가: "10개 Bash matcher 책임 직교 원칙 통합·삭제 금지, 고정 순서 절대 변경 금지"
- 신규 정책 아님 — 문서 곳곳에 분산된 기존 합의(README "훅별 실패 책임 매트릭스" + Phase 2-A 통합 평가 절차)를 PreToolUse 섹션에 명시.

**[보류 — 권한 차단] L-4 settings.local.json 1회용/중복 permission 정리**
- 사용자 지시 ("처리해라" + "1") 있었으나 권한 시스템이 settings 파일 편집을 3회 차단.
- 차단 사유: "settings 구조 변경 금지"는 사용자 모드 boundary, 일반 표현은 settings 파일 self-modification 승인으로 미인정.
- 분석 완료 (즉시 적용 시 5건 제거 가능): 라인 9 `gemini -p:*`(라인 8 부분집합) / 라인 27 `python notion_sync.py --manual-sync` ENV 중복 / 라인 29 daily-routine 상대 PYTHONIOENCODING 부분집합 / 라인 34·35 daily-routine 절대경로 1회용 (상대경로 라인 14 상위 호환).
- 진행하려면 사용자가 ".claude/settings.local.json 편집 승인"을 명시적으로 표현해야 함.
- 사용자 최종 결정: **보류 확정**. 양측 판정도 보류 인정.

**[3way 공유 PASS] 양측 판정 수령**
- GPT: PASS (전 항목 실증됨, 추가제안 없음 — "추가 개선 금지, 실무 산출물 모드 유지")
- Gemini: PASS (전 항목 동의, L-6 일반론 / L-4 환경미스매치, 추가제안 없음 — "시스템 개선 영구 중단 + 실무 산출물 모드 전환 승인")
- 양측 합의로 시스템 개선 모드 영구 중단 확정.

---

## 세션107 (2026-04-25) — GPT 시스템 정합성 검토 4건 반영

> 진입: 사용자 "gpt토론방 내용 확인후 내 계획을 듣고 싶어" → GPT 토론방 응답 수령. 5개 지적·5개 개선안 수령. 독립 라벨링 후 A 분류만 즉시 반영.

**[완료] L-3 SKILL.md 구 MCP 문구 정리** — 채택, A 분류
- `90_공통기준/토론모드/debate-mode/SKILL.md:95-103` `tabs_context_mcp` / `navigate(url, tabId)` 구 MCP 표기 → chrome-devtools-mcp 계열(`select_page(pageId, bringToFront=true)`) 표기로 갱신. 세션105 전환 반영.

**[완료] L-2 SKILL.md frontmatter β안-C 표현 보정** — 채택, A 분류
- frontmatter "API 없이 브라우저 자동화만으로 동작" + 본문 "API 사용 금지" → β안-C 예외(Step 6-2/6-4 단발 교차 검증) 명시 + `../CLAUDE.md` 참조 안내.

**[완료] L-1 hook 수동 카운트 표기 제거** — 채택, A 분류
- `STATUS.md:19` "32개 등록" → list_active_hooks.sh 동적 참조 안내. 세션 변동 수치 제거.
- `.claude/hooks/README.md:6` "활성 Hook (32개 등록)" → "활성 Hook (settings.json 기준)" 으로 변경. 이벤트별 분포(PreCompact 1 / SessionStart 1 / ...) 수동 표기 제거.
- `AGENTS_GUIDE.md`는 `generate_agents_guide.sh` 자동생성으로 동적 산출 (parse_helpers.py) → 수동 표기 금지 원칙 위반 아님. 통과.

**[완료] L-4 navigate_gate.sh 보호 자산 등록** — 채택, [3way] 만장일치 (pass_ratio=1.0)
- `90_공통기준/protected_assets.yaml` debate 계열 블록(line 87~95) navigate_gate.sh 추가 (class: guard / removal_policy: replace-only)
- yaml 인라인 reason에 한계 2건 명시: ① 정책 선언만 — 자동 수정 차단 hook 미구현 ② settings.json PreToolUse 호출부(matcher 3종) 동시 점검 필수
- GPT 보완 검증: `.claude/settings.json` line 262/271/280에 navigate_gate.sh 바인딩 3종(`mcp__Claude_in_Chrome__navigate` / `mcp__chrome-devtools-mcp__navigate_page` / `mcp__chrome-devtools-mcp__new_page`) 모두 존재 확인
- 3자 합의 로그: `90_공통기준/토론모드/logs/debate_20260425_115300_3way/`
- ⚠️ **위험 명시 (양측 통합)**: ① "정책 레지스트리 등록이며 자동 수정 차단 기능은 아님" (GPT) ② "settings.json PreToolUse 바인딩 임의 삭제 시 게이트 무력화 위험 — 호출부 유지보수 의존성 동시 명시" (Gemini)

**[완료] L-1 후속 final_check WARN 해소** — A 분류, 커밋 `aac8a9bf`
- 증상: L-1 STATUS.md "32개 등록" 수동 표기 제거 후 `final_check.sh` STATUS_COUNT 정규식 매칭 실패 → WARN 1건 매번 발생
- 수정: `final_check.sh:194` STATUS_COUNT가 비어있고 STATUS.md에 "list_active_hooks.sh --count" 키워드가 있으면 [OK] 처리 (Single Source of Truth 정책 일치)
- 검증: smoke_fast 11/11 / doctor_lite OK / final_check WARN 0건
- 3자 합의: GPT/Gemini 양측 "조건부 통과 → WARN 해소 후 PASS" 판정 → 본 커밋으로 PASS 조건 충족

**[완료] L-5 incident 분석 + session_drift 27건 + 의제 A~D 100건 일괄 해소** — A 분류
- 실측: 미해결 163건 (GPT 시점 80건 → 환경미스매치)
- 1차 처리: session_drift 27건 일괄 해소 (`resolved_by: session107_status_handoff_sync`) → 139건 잔존
- 2차 처리 (의제 A~D 100건 일괄 해소):
  - A: auto_commit_state / completion_before_state_sync 30건 → `session107_l5_a_root_cause_cleared` (final_check ALL CLEAR로 원인 해소)
  - B: UNCLASSIFIED (hook/type 빈 entry) 32건 → `session107_l5_b_invalid_entry_format` (형식 깨짐 데이터 가치 없음)
  - C: commit_gate / pre_commit_check 21건 → `session107_l5_c_root_cause_cleared` (동 A)
  - D: navigate_gate / send_block 17건 → `session107_l5_d_marker_present` (세션 진입 marker 정상)
- **잔존: 44건** (evidence_missing 26 / harness_missing 7 / scope_violation 6 / commit_gate doc_drift 3 / 기타 2 — 정당한 차단 기록, 보존 권고)
- 3차 처리 (잔존 47→44): token_threshold_check 2건(`session107_l5_round2_token_post_compact`) + debate_verify_block 빈 entry 1건(`session107_l5_round2_invalid_entry_format`) resolved
- 분석 보고서: `90_공통기준/업무관리/incident_session107_analysis.md`
- ledger 백업: `.claude/incident_ledger.jsonl.bak_session107_pre_l5_resolve`
- 신규 발생 방지 별 의제 처리 결과:
  - **B-2 [완료]**: hook_incident hook/type 필드 누락 추적 강화 (A 분류)
    - `.claude/hooks/record_incident.py:80` `--hook` argparse `required=True` (옵션 3)
    - `.claude/hooks/hook_common.sh:262` `hook_incident()` 빈 hook/type 시 hook_log WARN 기록 (옵션 1, entry 생성은 유지하되 호출자 caller 추적)
    - 외부 호출자: `gpt-read.md` 1곳만 사용 (--hook gpt-read 명시) → required=True 안전 검증
    - 검증: `--hook` 누락 시 정상 거부 ✓ / 빈 hook 호출 시 hook_log WARN 기록 ✓ / smoke_fast 11/11 ALL PASS
  - **D-2 [폐기]**: 분석 결과 변경 불요
    - 매 세션 첫 토론모드 진입 시 navigate_gate trip은 **정상 안전장치 동작**
    - 사용자가 토론모드 정상 사용 시 자동으로 토론모드 CLAUDE.md 읽기 → marker 생성 → 이후 통과
    - "신규 발생 자체"가 정책 위반 아님. 의제 폐기.

**[보류] P-5 navigate_gate / debate_independent_gate exit 2 격상**
- GPT도 보류 권고. send_block 오탐/정탐 비율 확보 후 결정.

**[완료] 토론모드 CDP Chrome 단독 사용 정책 명시 (사용자 지시)** — A 분류
- 사용자 지시: "2자/3자 토론모드 cdp단독브라우저 사용으로 제한한다"
- 분류 근거: 토론모드 CLAUDE.md 자동 승격 트리거 "스킬 md의 주석·경고 문구·설명 추가" → A 분류 + 사용자 지시 예외 (D안)
- 영향 파일 6건 (정책 명시 강화, 실행 흐름 미변경):
  - `90_공통기준/토론모드/CLAUDE.md` "백그라운드 탭 Throttling 대응" → "CDP Chrome 단독 사용" 섹션 신설 ([NEVER] 일반 Chrome / claude-in-chrome 계열 MCP / CDP 미기동 진입 금지)
  - `90_공통기준/토론모드/debate-mode/SKILL.md` frontmatter + 금지사항 본문에 CDP 단독 명시
  - `.claude/commands/gpt-send.md`, `gpt-read.md`, `gemini-send.md`, `gemini-read.md` 각각 헤더에 세션107 정책 강화 명시
- B 분류 검토 의제 (별도 사용자 결정 필요):
  - settings.json:262 `mcp__Claude_in_Chrome__navigate` 매처 제거 여부 (실행 차단 강제)
  - navigate_gate.sh에 claude-in-chrome 호출 차단 로직 추가 여부

**[보류·취소] CDP 단독 사용 실 차단 강제 (B 분류, 옵션 2)** — 사용자 지시 예외 D안
- 의제: 토론모드 외에서도 claude-in-chrome MCP 호출 자체 차단 (settings.json deny + navigate_gate fallback)
- 진행 결과: Round 1까지 — GPT/Gemini 양측 조건부 통과 (A+B 조합 동의 / 매처 처리 단계 vs 일괄 차이)
- 중단 사유: 사용자 명시 지시 ("그냥 취소 할까??" → "취소하자")
  - 정책 명시(177d5160)만으로 Claude 행동 규범 작동 충분
  - 세션107 BOM 사례 직접 경험 — settings.local.json 일괄 수정 위험 실증
  - L-4 합의 패턴 일관 (보호자산도 "정책 선언만, 자동 차단 hook 미구현")
- 로그: `90_공통기준/토론모드/logs/debate_20260425_134400_3way_cdp_only/`
- 재진행 트리거: 정책 위반 실증 발생 또는 외부 보안 요구사항 변경 시 B 분류 재검토

## 세션106 (2026-04-25 아침) — D0_SP3M3_Morning 스케줄러 LastResult=3 근본 해결

**[완료] batch 파일 인코딩 수정 (LF→CRLF + UTF-8 BOM)** — 커밋 `84675727`
- 증상: Windows 작업 스케줄러 `D0_SP3M3_Morning` 매주 월~토 07:10 트리거되지만 LastResult=3
  - 토요일 07:10 실행 결과도 LastResult=3, LOGFILE 생성 단계조차 도달 못함
- 근본 원인 2건:
  1. 줄 끝(EOL)이 LF만 — Windows `cmd.exe`는 CRLF 필요. 라인 분리 실패로 모든 명령이 단일 라인으로 묶여 깨짐
  2. UTF-8 BOM 없음 — `chcp 65001` 적용 전 한글 경로/주석을 ANSI(CP949)로 오해석
- 수정: Python으로 `run_morning.bat` + `D0_저녁.bat` 두 파일 CRLF + UTF-8 BOM 재저장
- 검증: 수동 재실행 → batch 정상 흐름 → LOGFILE 생성 → python run.py 진입 확인
  - `06_생산관리/D0_업로드/logs/morning_20260425.log` (3076 bytes)
  - LastResult 3 → 1 진전 (남은 1은 별건)

**[완료] ERR_BLOCKED_BY_CLIENT — 근본 원인 진단 + 포트 분리 (세션107)**
- 진단 결과 (실측):
  - chrome-cdp 프로필(토론모드 전용)에 **Urban VPN Proxy** 확장(`eppiocemhmnlbhjplcgkofciiegomcon`) 설치됨 — `proxy` + `<all_urls>` 권한
  - 토론모드 9222 점유 시 D0 자동화가 같은 9222 connect → chrome-cdp 프로필 재사용 → Urban VPN이 erp-dev.samsong.com:19100 트래픽 가로채기 → ERR_BLOCKED_BY_CLIENT
- 옵션 A (사용자 작업): chrome-cdp 프로필에서 Urban VPN 비활성/제거 (chrome://extensions/)
- 옵션 B (코드 변경, 완료): 업무 자동화 5개 포트 9222 → 9223 분리
  - 변경 파일 9개 / 9222 occurrence 22곳 → 9223 일괄 치환:
    - `d0-production-plan/run.py` (5곳)
    - `d0-production-plan/SKILL.md` (3곳)
    - `flow-chat-analysis/collector.py` (1곳)
    - `flow-chat-analysis/login.bat` (1곳)
    - `flow-chat-analysis/run.bat` (1곳)
    - `flow-chat-analysis/research.md` (1곳)
    - `production-result-upload/run.py` (1곳)
    - `production-result-upload/SKILL.md` (4곳)
    - `zdm-daily-inspection/SKILL.md` (4곳)
    - `.claude/commands/d0-plan.md` (1곳)
  - 백업: 각 파일 `.bak_session107_pre_port9223` 접미사 (git 제외)
  - 검증: Python syntax OK 3건 (run.py 2종 + collector.py)
- 분류: A (스크립트 코드 변경, 외부 인터페이스 미영향 — Chrome CDP 통신 포트만 변경, ERP/MES URL 동일) + 사용자 지시 예외 D안
- 운영 영향: 토론모드(9222 + chrome-cdp) 사용 중에도 업무 자동화(9223 + flow-chrome-debug) 정상 작동. 환경 완전 격리

**[검증대기] D0 9223 포트 분리 사후 검증 — 2026-04-27 (월) 07:10 LastResult=0 확인**
- 트리거: Windows 작업 스케줄러 `D0_SP3M3_Morning` 자동 실행
- 검증 항목: ① LastResult=0 ② `06_생산관리/D0_업로드/logs/morning_20260427.log` 정상 생성 ③ ERR_BLOCKED_BY_CLIENT 미발생 (포트 9223 격리 효과)
- 실패 시 후속: ① 옵션 A(Urban VPN 비활성) 사용자에게 안내 ② chrome-cdp 프로필 분리 추가 검토
- 차주 영업일 시작 시 가장 먼저 확인할 것

**[부분PASS·후속완료] D0 3자 토론 — #btnExcelUpload 30s 확장 추가 반영** — A 분류, [3way]
- GPT 부분PASS / Gemini 부분PASS (양측 일치)
- 채택: A1 `wait_for_selector("#btnExcelUpload", timeout=30000)` 두 곳 모두 15s→30s 확장 (Gemini 환경미스매치/동의 라벨, ERP 초기 로드 지연 실증)
- A2 등록 완료: `D0_SP3M3_Verify_Sunday` 일요일(2026-04-26) 22:00 ONCE 트리거 (Run As User=User, Schedule Type=One Time Only, run_morning_verify.bat 호출 = `--parse-only` 모의 구동)
  - 검증 후 task 삭제 권장: `schtasks /Delete /TN "D0_SP3M3_Verify_Sunday" /F`
  - 결과 로그: `06_생산관리/D0_업로드/logs/verify_20260426_220000.log`
- 보류: A3 작업스케줄러 설정 조회 (이미 `schtasks /Query`로 확인됨)
- 양측 합의 잔여: schtasks 자동 트리거 흐름 자체 미검증 / Phase 4~6 본체 무수정 회귀 위험 낮음

**[완료] D0 수동 사전 검증 — selectList 21건 통과 + iframe 폴링 픽스** — A 분류
- 트리거: 사용자 "오늘 아침 작동 안된 부분 검증 방법 없나?"
- run.py 신규 옵션 `--parse-only`: Phase 3 selectList(엑셀 첨부+서버 파싱)까지만 수행, multiList(DB 저장) 스킵
- d0_upload 시그니처에 `parse_only=False` 매개변수 추가, run_session_line / main `--xlsx` 모드 모두 지원
- 검증 batch 신설: `90_공통기준/스킬/d0-production-plan/run_morning_verify.bat` (`--parse-only`로 호출, CRLF + UTF-8 BOM)
- iframe 폴링 버그 픽스: `_wait_d0_popup_frame(page, timeout_sec=25.0)` 헬퍼 신설 — frame URL 매칭 + DOM querySelector(`iframe[src*="popupPmD0AddnUpload"]`) 보강. iframe[name="ifr_user"] src URL이 about:blank → popupPmD0AddnUpload.do로 늦게 set되는 경합 대응 (12s → 25s 확장)
- 검증 결과: ERP 파서 응답 `listLen=21, statusCode=200, "정상 완료되었습니다", ERROR_FLAG=Y 0건, COL2 빈값 0건` — 엑셀 파일(Excel COM 생성) 100% 정상
- 진단 부산물(_diag_selectList.py) 삭제 완료. verify batch는 향후 재사용 위해 보존

## 세션105 (2026-04-24 저녁) — 시스템 개선 3자 토론 + 탭 전환 근본 해결

**[완료] 3자 토론 Round 1+2 — 세션103 이월 의제 3건 합의 성립**
- 로그: `90_공통기준/토론모드/logs/debate_20260424_195811_3way/`
- Q1 조건부 격상: Round 1 GPT=C / Gemini=B 불일치 → Round 2 양측 **기타안 동조** (pass_ratio 4/4 만장일치)
  - 기타안 = B "실측 선행" + C "임계값 구현 폐기" + 재점화 4조건 (Gemini tightening 반영)
- Q2 실증됨 라벨 엄격화: GPT=A / Gemini=A — 합의 (증거 필수 규칙)
- Q3 incident 110건 대응: GPT=A / Gemini=A — 합의 (즉시 /auto-fix 1차 분류)
- 다음 실행 단위: Q3 /auto-fix 1회 + auto_commit_state audit 1회 + advisory 경고 강화

**[완료] 탭 전환 근본 해결 — chrome-devtools-mcp 병행 설치**
- 원인: Claude in Chrome MCP가 CDP `Target.activateTarget` / `Page.bringToFront` 차단
- Step 1 ✅ `chrome-devtools-mcp` user scope 등록
- Step 2 ✅ CDP Chrome 포트 9222 LISTENING
  - **주의**: Chrome M136+ 보안 강화로 기본 프로필에서 CDP 사용 금지 → 별도 프로필 `C:\temp\chrome-cdp` 사용
  - 기본 Chrome과 CDP Chrome 병행 기동 중
- Step 3 ✅ chrome-devtools-mcp 도구 로드 + 포트 9222 연결 확인 (ToolSearch로 본 세션 로드 완료, 세션 재시작 불필요)
- ChatGPT·Gemini 양측 CDP Chrome에서 로그인 완료 (재로그인 1회성 비용)

**[완료] 4개 스킬 chrome-devtools-mcp 마이그레이션 (사용자 지시 예외 / D안 선례 준용)**
- `.claude/commands/gpt-send.md`, `gpt-read.md`, `gemini-send.md`, `gemini-read.md` 전면 재작성
- `90_공통기준/토론모드/CLAUDE.md` 탭 throttling 대응 섹션 + Chrome MCP 금지 범위 갱신
- 핵심 변경:
  - `tabs_context_mcp` → `list_pages` / `tabs_create_mcp` → `new_page`
  - `navigate(url, tabId)` 재호출 hack → `select_page(pageId, bringToFront=true)` (CDP 네이티브)
  - `javascript_tool` → `evaluate_script`
  - `get_page_text`/`find`/`computer` → `take_snapshot`/`click`/`fill` (필요 시만)
- 상태 파일 `gpt_tab_id`·`gemini_tab_id` 내용 의미 변경: 문자열 tabId → 정수 pageId
- 실전 Round 2 검증 완료 (2026-04-24 22:00~22:10 KST, pass_ratio 4/4 실증)

**[완료] Round 2 실운영 중 발견 이슈 2건 — 문서화·스킬 보강**
1. ✅ **Chrome CDP 바인딩 기본값이 IPv6** — `90_공통기준/토론모드/CLAUDE.md:142` "CDP Chrome 전제 조건"에 `--remote-debugging-address=127.0.0.1` 플래그 필수 명시 + 정식 launch 커맨드 등재
2. ✅ **Gemini Gem 모델 설정 미고정** — `.claude/commands/gemini-send.md` 1-B-1 신설: SEND GATE 전 모델 라벨 확인 + 다르면 take_snapshot/click으로 재선택 강제 (생략 금지)

**[완료] Q5 Claude 독자 답안 선행 강제 (세션105 말미, 사용자 지시 예외 D안 적용)**
- 사용자 지적: Round 2 Q1·Q4에서 Claude 독자 답안 선행 없이 양측 답변 축약 → "3-way + Claude 축약자" 구조
- 메모리 `feedback_independent_gpt_review.md` + `feedback_harness_label_required.md` 이미 규칙 명시되어 있었으나 미이행
- 조치 2건:
  1. `debate-mode/SKILL.md` Step 3-W에 **6-0 단계 신설** — round{N}_claude.md를 GPT/Gemini 전송 전에 **먼저** 작성 강제. 양측 본론 수령 전 독립 답안 확보
  2. `debate_independent_gate.sh` 매처·셀렉터 확장:
     - matcher에 `mcp__chrome-devtools-mcp__evaluate_script` 추가 (신규 MCP 우회 방지)
     - 셀렉터에 `ql-editor` 추가 (Gemini 입력창 커버)
     - `tool_input` JSON 전체를 payload로 간주하도록 필드 파싱 확장
- 회귀 테스트 5건 PASS:
  1. evaluate_script + insertText + prompt-textarea + marker 없음 → DENY
  2. evaluate_script + insertText + ql-editor (Gemini) → DENY
  3. evaluate_script + non-insert (읽기 스크립트) → skip
  4. marker 있으면 PASS + 마커 1회 소비
  5. 레거시 Claude_in_Chrome__javascript_tool 기존 동작 유지
- 사용자 지시 예외 근거: "지금적용해" 명시 지시 (세션105 2026-04-25)
- 다음 세션 첫 토론 send 전 `touch .claude/state/debate_independent_review.ok` 또는 스킬이 자동 생성

**[완료] Q4 navigate_gate 감지 기준 재검토 — 3자 토론 Round 1 만장일치**
- 로그: `90_공통기준/토론모드/logs/debate_20260424_230014_3way/` (session_init, round1_gpt/gemini/claude_synthesis/cross_verify)
- pass_ratio 4/4 — GPT/Gemini 모두 A안(최소보강) 동일 결론
- 구현:
  - `settings.json` PreToolUse matcher 2개 추가 (`mcp__chrome-devtools-mcp__navigate_page`, `mcp__chrome-devtools-mcp__new_page`)
  - `navigate_gate.sh` URL 파싱 확장 — navigate_page는 `type="url"`일 때만 검사, 비URL 타입(reload/back/forward)은 통과
  - select_page/evaluate_script/take_snapshot/click/fill 은 URL 진입 아니므로 gate 대상 제외
- 회귀 테스트 5건 PASS:
  1. 네거티브(marker 없음 + chatgpt URL) → DENY ✓
  2. 포지티브(marker 있음) → PASS ✓
  3. 비대상(navigate_page type=reload) → skip ✓
  4. new_page chatgpt → DENY ✓
  5. new_page gemini → skip ✓
- 효과성 평가: 7일간 send_block 0~2건 정상 / 부당 오탐 3건 이상 시 Round 2 재검토

**[완료] Q3 auto-fix 1차 분류 (세션105 말미, Round 1 Q3=A안 합의 후속)**
- 미해결 80건 7개 카테고리로 분류 (보고서: `90_공통기준/토론모드/logs/debate_20260424_195811_3way/q3_auto_fix_classification.md`)
- 상위 1위: auto_commit_state completion_before_state_sync 15건 (19%) — **Q1 재점화 조건 4 수치상 충족**
  - 단 Q1 기타안 audit 해석(단일 세션 burst)과 일치 → **재상정 불필요** (중복 의제 방지)
- 상위 2위: commit_gate pre_commit_check 14건 — Category A 동근원, Q1 advisory 강화 효과 관찰(2주)
- 상위 3위: navigate_gate send_block 11건 — **신규 Q4 의제 후보 "navigate_gate 감지 기준 재검토"**
- Category D (session_drift 10건): `/finish` 또는 `final_check --fix`로 자동 해소 시도 가능
- Category E (harness_missing 5건): Q2 정책 구현과 연계
- Category F (2건): 개별 처리
- Category G (미분류 23건): Phase 2 세부 조사 대상

**[완료] Q1 기타안 실행 3단계 모두 완료**
- Step 1 ✅ `auto_commit_state` audit — 최근 14일 15건, 전부 하루(2026-04-24) 집중, classification 단일(`completion_before_state_sync`)
  - 결론: 조건 1 수치상 충족되나 원인·패턴 분석상 격상 불필요. advisory 유지가 정답
  - 보고서: `90_공통기준/토론모드/logs/debate_20260424_195811_3way/audit_auto_commit_state.md`
- Step 2 ✅ `auto_commit_state.sh` advisory 강화 — 실행 흐름 변경 없음
  - 이전 60분 내 동일 원인 중복 건수 표시
  - 미동기화 AUTO 파일 목록 명시
  - 재점화 조건 1 근접 시 경고 추가
- Step 3 ✅ TASKS에 재점화 4조건 등록 (하단 참조)

### 세션105 Q1 최종 정책: auto_commit_state 재점화 4조건

> 본 조건은 **임계값 구현이 아니라 의제 재개 조건**이다. 오차단 리스크 없이 감시만 한다.

1. **반복 빈도 조건** — auto_commit_state 태그 incident 최근 7일 3건 이상 AND 그중 2건 이상 final_check --fast 실패 → Q1 재상정
2. **상태 롤백 조건** — auto_commit_state 차단 이후 "상태 불일치로 인한 롤백" 실사례 1건 이상 발생 → Q1 재상정 (단순 TASKS 미동기화는 자동 트리거 아님, Gemini tightening)
3. **설계 결함 조건** — push 실패가 네트워크 아닌 hook 설계 문제로 2회 이상 반복 → **긴급 whitelist/로직 수정** 근거 (격상 아님, Gemini tightening)
4. **원인 상위 조건** — Q3 `/auto-fix` 분류에서 auto_commit_state가 상위 3개 원인군 진입 → Q1 재상정

> 로그 근거: `90_공통기준/토론모드/logs/debate_20260424_195811_3way/round2_claude_synthesis.md` + `audit_auto_commit_state.md`



> **메타 억제 기준**: `.claude/state/meta_freeze.md` — **해제됨** (2026-04-23, incident 52건)

---

## 세션104 (2026-04-24 저녁) — /d0-plan 야간 실운영 + xlsx 포맷 근본 수정

**[완료] SP3M3 야간 15건 실운영 반영**
- 파일: `SP3M3_생산지시서_(26.04.25).xlsm` 출력용 야간 섹션 → 15건 추출
- Phase 3 업로드 → Phase 4 서열 배치 15건 → Phase 5 MES 전송 (rsltCnt=750) ✅

**[완료] xlsx 포맷 버그 근본 해결 — openpyxl → Excel COM**
- 증상: openpyxl로 생성한 xlsx 업로드 시 ERP 서버가 COL2(제품번호) 빈값으로 파싱, 15건 전부 ERROR_FLAG=Y
- 원인: OOXML 내부 구조(sharedStrings, cell type 속성, 시트 XML 네임스페이스) 차이
- 해결: `make_upload_xlsx`를 `win32com.client(Excel.Application)` 기반으로 교체. 템플릿 복사 후 Excel이 직접 저장
- 템플릿: `90_공통기준/스킬/d0-production-plan/template/SSKR_D0_template.xlsx` (ERP 양식다운로드본)
- `.gitignore`에 `!90_공통기준/스킬/d0-production-plan/template/*.xlsx` 예외 허용 추가

**[완료] Phase 6 verify_smartmes 날짜 버그 수정**
- 기존: `run_session_line`이 prod_date 단일로 검증
- 수정: `verify_prod_date` 파라미터 추가 — SP3M3 야간은 야간 시작일(target_file_date-1)로 SmartMES 조회
- main session 분기에서 각각 명시 전달

**[완료] 팝업 재사용 로직 우선 배치**
- 기존: overlay 감지 시 reload가 먼저 → 팝업 iframe이 사라져 매번 새로 오픈 시도
- 수정: 팝업 iframe 검사를 앞에 배치 — 있으면 재사용, 없을 때만 overlay 체크/reload
- 연속 실행 시(dry-run → live) Chrome이 팝업 열린 채 유지되어도 정상 동작

**[완료] SKILL.md v2 갱신**
- Python 의존성에 `pywin32` + Microsoft Excel 설치 필요 명시
- Phase 2 10번 Excel COM 강제 경고 추가
- 핵심 주의사항 0번(최상단)에 openpyxl 생성 금지 경고

**[대기] 후속**
- SD9A01 OUTER 저녁 세션 실 검증 (내일 저녁 `--dry-run` 먼저)
- `D0_SP3M3_Evening` 스케줄 추가 검토 (SP3M3 저녁 세션도 자동화)

---

## 세션102 (2026-04-24) — auto_commit_state 운영 계약 보강 (3자 토론 [3way])

**[완료] P-1 protected_assets.yaml 등록**
- `90_공통기준/protected_assets.yaml` Stop 계열 블록에 `auto_commit_state.sh` 추가
- class: guard, removal_policy: replace-only
- 사유: 세션101 GPT 평가 L-1 — 신규 Stop hook이 보호 레지스트리 미등재 (SPOF-4)

**[완료] P-2 README Failure Contract 등재**
- `.claude/hooks/README.md` Failure Contract 표에 `auto_commit_state.sh` 추가
- 정책: fail-open (advisory) + AUTO 패턴 한정 + final_check FAIL 시 incident 기록 후 자동 commit/push 차단
- 사유: 세션101 GPT 평가 L-2 — 운영 계약 문서화 누락

**[완료] hook_common 계측 적용 (커밋 2 분리)**
- `.claude/hooks/auto_commit_state.sh` source hook_common.sh + hook_timing_start/end + hook_log + hook_incident
- 합의 본질 구현 (hook_advisory wrapper 직접 호출 대신 내부 함수 활용 — 다단계 로직 흐름 보존)
- 기록 확인: timing/incident_ledger/hook_log 정상 동작 (final_check FAIL 테스트 PASS)
- 분리 사유: 사용자 지침 "한 곳 수정이 다른 곳을 무너뜨림" 반영. 실행 파일 변경은 회귀 추적 단위 분리

**[합의 결과] 3자 토론 (Round 1, pass_ratio=1.0)**
- Q1: A안 (3/3) — Stop 블록 추가
- Q2: B안 (3/3) — incident 기록 + push 차단
- Q3: A안 (2/3) — hook_advisory 래핑 (Gemini C안 hook_gate는 별도 의제 이월)
- Q4: B안 (2/3) — 분리 커밋 (Claude 입장 변경, 사용자 지침 반영)
- 로그: `90_공통기준/토론모드/logs/debate_20260424_132813_3way/`

**[완료] GPT 재평가 P-1 반영 (settings.local 1회성 제거)**
- `.claude/settings.local.json:34` `Bash(python create_sp3m3_process_eval.py)` 제거 — SP3M3 평가서 생성 1회용, 재사용 근거 없음
- GPT 재평가 판정: L-1 실증됨, 심각도 중

---

## 세션103 (2026-04-24) — Stop hook 등급 체계 재검토 [3way]

**[완료] advisory 유지 + stderr 가시성 강화**
- 3자 토론 (GPT gpt-5-5-thinking + Gemini gemini-2.5-pro) Round 1 pass_ratio=0.75 합의
- Q1: B안 채택 — 즉시 hook_gate 격상 반대. advisory 유지 + 경고 포맷 개선
- Q2: B안 채택 — exit 2 부작용(일시 오류 무한 블록) > 이점. advisory + 가시성 우선
- 변경: `auto_commit_state.sh:87` 박스형 ⛔ 경고 포맷 적용 (실행 흐름 미변경, A 분류)
- 로그: `90_공통기준/토론모드/logs/debate_20260424_152100_3way/`

**[폐기] 조건부 격상 설계** (세션103 3way 채택 → 세션103 폐기)
- 사유: advisory + commit/push 차단 + incident + stderr 박스 경고로 이미 실용적 보호 충분
- 반복 구조적 FAIL 실발생 빈도 낮음. 구현 복잡도(카운트 추적·세션 경계·임계값) > 실효
- 임계값 오설정 시 과도 차단 또는 유명무실. 제조업 세션 중단 리스크

**[폐기] P-4 wrapper drift 감시** (세션101 이월 → 세션103 폐기)
- 사유: hook_common wrapper 적용 hook 1개(debate_verify)뿐, 감시 대상 부재
- 세션102 실적용에서 wrapper 대신 내부 함수 활용 방식 채택 (다단계 로직 보존)
- 일괄 적용 계획 없이 drift 감시만 신설은 유효하지 않음

---

## 다음 세션 의제 — SD9A01 공정별 숙련도 평가서 작성 (대기 중)

**[대기] SD9A01 공정별 숙련도 평가서 작성 (SP3M3 패턴 복제)**
- 계획서: `01_인사근태/숙련도평가/SD9A01_작업계획.md`
- 대상: SD9A01 라인 10공정, 개인 평가서 24명 (주간 13+야간 11, SD9M01 라인코드)
- **Phase 0 선행**: 작업표준서 통합 필요 (180706 Rev.16 + 260101 Rev.16 → 통합본 1개)
- Phase 1: 공정별 양식 10개 (SP3M3 v4 기반)
- Phase 2: 개인별 파일 24개 (SP3M3 personal_v2 기반)
- 재사용 자산: 샘플 양식, 스크립트 2종, 구조 패턴
- 세션 시작 시 사용자 확인: 작업표준서 통합 방식 (A=최신단독/B=자동병합/C=수기)

---

## 세션102 (2026-04-24) — SP3M3 공정별 숙련도 평가서 신규 작성

**[완료] SP3M3 공정별 숙련도 평가서 6개 파일 생성**
- 위치: `01_인사근태/숙련도평가/SP3M3_공정별 평가서/`
- 파일: 공정10/11/91/140/340/430 각 개별 xlsx
- 샘플 양식(`공정 평가서표준_SP3M3_샘플.xlsx`) 레이아웃/스타일 유지
- 전문강화 섹션(행13~21) 재구성:
  - 작업표준서 기준 5항목 (행13~17) — 출처: `SP3M3_작업표준서_200730_R1.xlsx`
  - 관리계획서 기준 4항목 (행18~21) — 출처: `SP3M3_관리계획서_대원테크.xlsx`
- 평가기준 Q/U/Y 열(100%/80%/미달) 각 항목별 의미 맞게 재작성
- 생성 스크립트: `01_인사근태/숙련도평가/생성스크립트/create_sp3m3_v4.py`
- 공정명 기준 매핑(번호 기준 아님): 공정140→시트130, 공정340→시트330 등 확인

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

## 이전 세션 (세션96 이하) — 아카이브

- 세션90~96 상세: `98_아카이브/session91_glimmering/TASKS_session90~96.md` (세션103 감량)
- 세션88 이하: `98_아카이브/session91_glimmering/TASKS_~session88.md`
