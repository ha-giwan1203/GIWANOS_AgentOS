# 업무리스트 프로젝트

@.claude/rules/cowork-rules.md
@.claude/rules/data-and-files.md

자동차 부품 제조업(삼송 G-ERP) 업무 자동화 저장소.

## 도메인 진입

| 키워드 | 도메인 문서 |
|--------|-----------|
| 토론 / 토론모드 / 3자 토론 / 3-way / Claude×GPT×Gemini / 공동작업 / 공유 | `90_공통기준/토론모드/CLAUDE.md` → `/debate-mode` 스킬 |
| 정산 / 조립비 / settlement | `05_생산실적/조립비정산/CLAUDE.md` |
| 라인배치 / OUTER / ERP 라인배정 | `10_라인배치/CLAUDE.md` |
| MES 업로드 / 실적 올려 | `90_공통기준/스킬/production-result-upload/SKILL.md` |
| 일상점검 / ZDM | `90_공통기준/스킬/zdm-daily-inspection/SKILL.md` |
| 급여 / 단가 | `02_급여단가/CLAUDE.md` |
| 생산계획 / 계획 | `04_생산계획/CLAUDE.md` |
| 생산관리 / 관리 | `06_생산관리/CLAUDE.md` |

도메인 키워드 감지 시 해당 문서를 먼저 읽는다.

## 상태 원본

작업 상태는 **TASKS.md에만 기록**한다.
- TASKS: `90_공통기준/업무관리/TASKS.md`
- HANDOFF: `90_공통기준/업무관리/HANDOFF.md`
- STATUS: 각 도메인 하위 `STATUS.md`
- 우선순위: TASKS.md → STATUS.md → HANDOFF.md → Notion
- 현업 업무: `90_공통기준/업무관리/업무_마스터리스트.xlsx` 우선. AI 작업: TASKS.md 우선
- Git이 기준 원본. Notion은 보조. 중복 유지 금지

## 완료 판정 (사람/GPT 판정 기준 — 자동 게이트 아님)

기준 문서 확인 + 반영 위치 확인 + Git 실물 존재 + TASKS.md 비충돌 → PASS
미충족 시: 정합 / 부분반영 / 미반영 / 보류 / 기준 미확인 / 임시검토

> completion_gate는 TASKS/HANDOFF 갱신 여부만 검사하는 최소 게이트다. 위 4개 기준 전체를 자동 검증하지 않는다.

## 종료 시 갱신
1. TASKS.md → 2. 도메인 STATUS.md → 3. HANDOFF.md → 4. Notion (필요 시)

## 외부 모델 호출 (3-tool 합의안, 2026-04-18)

워크플로우 설계 주체는 항상 Claude. GPT/Gemini는 입력 제공자로만 호출.

| 도구 | 호출 경로 | 사용 시점 |
|------|----------|----------|
| GPT (웹) | `/gpt-send`, `/gpt-read` | 토론, 추론·창의·아이디어 다변화, 반대논리 검증 |
| Gemini (웹) | `/gemini-send`, `/gemini-read` | 토론, 멀티턴 대화 |
| Gemini (CLI minion) | `/ask-gemini` | 빠른 단발 질의, WebFetch fallback, 대용량/멀티모달 |

**원칙**:
- Claude가 호출 시점·입력·검증 절차를 설계
- GPT/Gemini 응답은 무결성 검증 후 채택 (실물 파일/Git/실증 데이터 대조)
- 도메인 한정 발상 금지 — 강점 기반 분담
- **상호 감시**: 3자 토론 시 단일 모델 단독 통과 금지 — GPT 답은 Gemini 검증, Gemini 답은 GPT 검증, Claude 설계는 양측 검증 (`90_공통기준/토론모드/CLAUDE.md` "상호 감시 프로토콜")
- 자세한 합의안: 메모리 `project_three_tool_workflow.md`

## Self-X Layer 1 — Health Summary 의무 (B1 3way 만장일치, 2026-04-21)

**[MUST]** Claude는 **프로젝트성 작업** 첫 사용자 응답에 **health summary 1줄을 포함**한다.
- 형식: `[health] N OK · M WARN · K CRITICAL` (정상 시 `[health] N OK`만)
- 출처: `.claude/self/summary.txt` (SessionStart에서 `health_check.sh` 자동 갱신, **stderr 채널로 컨텍스트 주입**)
- WARN/CRITICAL 시 자동 펼침 (각 1줄, 상세는 `.claude/self/HEALTH.md`)
- 면제: 단순 인사·확인·일반 대화 (프로젝트 키워드 미매칭)
- 강제 메커니즘: `UserPromptSubmit` hook(`health_summary_gate.sh`)이 프로젝트 키워드 매칭 시 advisory 리마인더 stderr 주입 (사용자 메시지 차단 없음, Phase 2-C에서 hard gate 검토)
- 정책: Layer 1은 감지만 (자동 조치 절대 금지). 출처: `90_공통기준/토론모드/logs/debate_20260421_133506_3way/`

invariants 정의: `90_공통기준/invariants.yaml` (8개 + 정책 5개 + 메커니즘 4개). 평가: `.claude/self/diagnose.py`.

## 운영 안정성
- settings/hook 파일 변경 후 반드시 세션 재시작 (변경사항은 세션 시작 시 캐싱됨)
- 장시간 세션 방치 금지 — 도메인/의제 전환 시 세션 재시작 권장
- 공통 모듈(hook_common 등) 수정 시 `grep -r` 호출부 전수 확인 선행
- 파일 변경 후 TASKS/HANDOFF 갱신을 커밋 직전에 함께 수행 (completion_gate 반복 방지)
- Windows PowerShell 세션에서는 `bash`가 PATH에 없을 수 있다. Bash가 필요하면 `.claude/scripts/run_git_bash.ps1 '<command>'` 또는 `C:\Program Files\Git\bin\bash.exe -lc '<command>'`를 사용한다.

## /rewind 한계 (2026-04-18 3자 토론 합의)
- `/rewind`(Esc×2)는 **Claude가 만든 코드 변경만** 되돌린다. Git 대체재가 아니다.
- bash 명령으로 수행한 변경(`rm`, `mv`, `cp`, 외부 스크립트 실행, ERP/MES 업로드)은 **추적·복구 불가**.
- 저장소는 Bash 훅·외부 스크립트·G-ERP 연동이 많으므로, 중요한 변경은 반드시 `git commit` 후 작업한다.

## 문서 조회 우선순위 (2026-04-18 3자 토론 합의)
- **라이브러리/SDK/API 문서 조회**: `context7` MCP 우선 사용 (`mcp__context7__query-docs`, `resolve-library-id`). WebSearch는 fallback.
- **일반 리서치·최신 뉴스·사례 조사**: WebSearch 우선.
- 이유: context7은 공식 저장소에서 최신 버전별 문서를 가져와 학습 데이터 오래됨 문제를 해소한다.

## hook vs permissions 역할 경계 (2026-04-19 의제5 3자 토론 합의)

> 배경: `.claude/settings.local.json` permissions.allow가 110개까지 누적되며 1회용 16건 + 완전 중복 2건이 섞여 들어온 문제를 근본 해결. 상세 로그: `90_공통기준/토론모드/logs/debate_20260418_190429_3way/`.

### 경계 원칙
- **permissions = 도구 호출 허용 on/off 게이트** — "이 Bash/Write/MCP 호출 자체를 허용할지"
- **hook = 호출 시점 맥락 검증 (조건부 게이트)** — "호출 시점의 지시문/상태/커밋 기준 등 맥락이 맞는지"
- **기능 직교**: 동일 보안 목적이라도 permissions와 hook 중 하나만 씀. 중복 금지
- **포괄 Bash 허용 vs dedicated tool**: 포괄 `Bash(cat:*)`·`Bash(grep:*)` 등은 fallback. **우선순위는 Read/Grep/Glob** 전용 도구

### 신규 추가 5단계 의사결정 트리
permissions나 hook을 추가할 때 위에서 아래로 순서대로 묻는다.

1. **전역 규칙인가 일회성 예외인가?** — 1회용(PID·URL·특정 경로 하드코딩)이면 **등록하지 않는다**. 포괄 패턴(`Bash(echo:*)` 등)이 이미 있으면 그걸 쓴다. 포괄이 없으면 포괄 등록을 고려한다.
2. **도구 호출 허용 문제인가?** — 호출 자체를 막거나 풀어주는 문제면 `permissions`.
3. **호출 시점 맥락 문제인가?** — 호출 조건(지시문 읽음·커밋 기준 갱신 등)에 따라 허가가 달라지면 `hook`.
4. **둘 다 필요한가?** — 허용은 permissions로, 조건은 hook으로 분리. 한 곳에 섞지 않는다.
5. **기록/만료 정책이 필요한가?** — 일시적 허용이면 `.claude/state/` 또는 `hook_log.jsonl`에 기록하고 만료 조건을 문서화.

### settings 계층 분리 가이드 (쟁점 G — 선제조건 검토만, 실물 이동은 세션72 이월)
- **팀 공용 정책** (전역 허용·전역 hook): `.claude/settings.json` 또는 기준 문서 (Git 커밋)
- **개인·세션성 예외**: `.claude/settings.local.json` (gitignore 또는 최소 범위)
- 재분류 인벤토리: `90_공통기준/토론모드/settings_inventory_20260419.md`

### 재발 방지 훅
- `.claude/hooks/permissions_sanity.sh` (advisory): 1회용 패턴·완전 중복 자동 탐지 → stderr 경고 + `hook_log.jsonl` 기록. 차단 없음. 60분 캐시.
- Phase 2-B(세션71 후속 또는 세션72): `completion_gate.sh` 소프트 블록 — 동일 1회용 패턴 3회 누적 탐지 시 사용자 명시적 확인 프롬프트. **하드페일 사용 안 함** (제조업 급한 세션 중단 리스크 회피)

## 훅 등급 + 에러 전파 정책 (2026-04-19 의제5 Gemini 제안·GPT 승격)

> 36개 `.sh` 훅이 맞물린 상태에서 특정 훅 exit 1 전파 정책이 제각각이던 문제를 표준화. hook_common.sh 공통 래퍼 + .claude/hooks/README.md 등급 분류 테이블 참조.

### 훅 등급 3종
- **advisory (경고성)**: 실패해도 세션 계속. `exit 0` 강제. stderr 로그만. `|| true` 허용 명시. 예: `permissions_sanity.sh`, `auto_compile.sh`, `notify_slack.sh`
- **gate (차단성)**: 실패 시 상위 도구 호출 차단. `exit 2` + JSON `decision=deny` 병행(belt-and-suspenders). `|| true` 금지. 예: `block_dangerous.sh`, `commit_gate.sh`, `date_scope_guard.sh`, `protect_files.sh`, `evidence_stop_guard.sh`, `stop_guard.sh` (Phase 2-B 세션72 exit 2 전환 완료). `debate_verify.sh`는 incident 18건 잔존으로 Phase 1 advisory 유지 (Phase 2-C 재평가).
- **measurement (계측)**: 실패 영향 없음. `exit 0` 강제. timing·통계만 기록. `trap ERR` 무시. 예: timing 래퍼, `hook_log`

### 공통 래퍼 함수 (hook_common.sh 정의)
- `hook_advisory <hook_path>` — 실패 시 stderr 로그 + exit 0
- `hook_gate <hook_path>` — 실패 시 exit 2 전파
- `hook_measure <hook_path>` — trap ERR 예외 무시, timing만

### Phase 2-B 적용 현황 (2026-04-19 세션72)
- **exit 2 + timing 배선 완료 (6개 gate)**: `commit_gate.sh`, `block_dangerous.sh`, `date_scope_guard.sh`, `protect_files.sh`, `evidence_stop_guard.sh`, `stop_guard.sh`
- **timing만 배선 (Phase 2 승격 보류)**: `debate_verify.sh` — `incident_ledger` `debate_verify` 태그 18건 잔존. incident 7일 0건 달성 시 Phase 2-C에서 exit 2 전환
- **completion_gate.sh 소프트 블록 추가**: 최근 7일 permissions 1회용 패턴 동일 라벨 3회 이상 누적 시 deny 1회(60초 쿨다운) — 하드페일 없음
- **나머지 훅 등급 분류**: `.claude/hooks/README.md` 표 참조. 일괄 timing 배선은 Phase 2-C 이월
- 확장 여지: 복구(cleanup/teardown) 등급 — Gemini 제안, 세션73+ 평가

## 금지
- 원본 xlsx/docx/pdf 직접 수정
- 승인 없는 파일명/시트명/컬럼명 변경
- 검증 없이 값 덮어쓰기
- Git 미확인 추측 답변
- 미푸시 상태를 완료로 간주
- Claude 설명만 듣고 PASS
