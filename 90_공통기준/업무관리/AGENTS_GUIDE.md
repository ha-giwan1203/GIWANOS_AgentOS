# 업무 자동화 에이전트 가이드

> 이 문서는 프로젝트의 자동화 구성요소를 6계층으로 정리한 운영 맵이다.
> 새 세션 시작 시 전체 구조를 파악하는 참조 문서로 사용한다.

---

## 아키텍처 개요

```
현업 계층  →  상태 계층  →  협업 계층  →  검증 계층  →  실행 계층  →  감시 계층
```

---

## 1. 현업 계층

현업 업무 일정, 남은 과제, 반복 업무, 마감일의 기준 원본.

| 구성요소 | 경로 |
|---------|------|
| 업무 마스터리스트 | `90_공통기준/업무관리/업무_마스터리스트.xlsx` |

AI 작업의 원본이 아님. 현업 업무 질문은 이 파일을 먼저 확인.

---

## 2. 상태 계층

AI 작업 상태의 원본. 판정 우선순위: TASKS > STATUS > HANDOFF > Notion

| 구성요소 | 경로 | 역할 |
|---------|------|------|
| TASKS.md | `90_공통기준/업무관리/TASKS.md` | 상태 원본 (1순위) |
| STATUS.md | `90_공통기준/업무관리/STATUS.md` | 운영 요약, 재개 위치 |
| HANDOFF.md | `90_공통기준/업무관리/HANDOFF.md` | 세션 인수인계 메모 |
| 도메인 STATUS | `05_생산실적/조립비정산/STATUS.md` 등 | 도메인별 재개 위치 |

---

## 3. 협업 계층

Claude-GPT 공동작업 + 운영 원칙.

| 구성요소 | 역할 |
|---------|------|
| CLAUDE.md (루트) | 프로젝트 전체 운영 원칙 |
| 도메인 CLAUDE.md | 업무별 세부 규칙 |
| Plan-First 워크플로우 | research.md → plan.md 승인 → 구현 |
| GPT 공동작업 | 작업 완료 → push → GPT 검증 → PASS/FAIL |

---

## 4. 검증 계층

자동/반자동 품질 검증 체계.

<!-- AUTO_HOOKS_START -->

### Hooks (.claude/hooks/) — 36개 활성 (settings.json+settings.local.json 기준)

> 상세: `.claude/hooks/README.md` 참조. 아카이브: `.claude/hooks/_archive/`
> 이 섹션은 `generate_agents_guide.sh`가 자동 갱신. 수동 편집 시 덮어쓰기됨.

| 스크립트 | 역할 |
|---------|------|
| `session_start_restore.sh` | 세션 시작 시 이전 상태 복원 (compact 저장 → 복원) |
| `precompact_save.sh` | 컨텍스트 압축 직전 핵심 상태 저장 |
| `risk_profile_prompt.sh` | 프롬프트 위험 키워드 감지 → .req 파일 생성 |
| `block_dangerous.sh` | 극단 파괴 명령 + 보호 경로 삭제/이동 차단 |
| `commit_gate.sh` | git commit/push 전 final_check 강제 (--fast/--full 자동 판정) |
| `date_scope_guard.sh` | ZDM/일상점검 일요일·일괄범위·MM/DD 차단 |
| `evidence_gate.sh` | req있고 ok없으면 위험 실행 deny |
| `protect_files.sh` | 원본 엑셀/아카이브/기준정보 수정 차단 |
| `state_rebind_check.sh` | 상태 바인딩 정합성 검사 |
| `mcp_send_gate.sh` | Chrome MCP 토론모드 전송 전 지침 읽기 강제 (SEND GATE) |
| `harness_gate.sh` | 토론모드 GPT 응답 후 하네스 분석 없이 행동 차단 (채택/보류/버림 + 독립 견해 + 실물 근거 복합 조건) |
| `instruction_read_gate.sh` | GPT 전송 전 ENTRY.md+토론모드 CLAUDE.md 읽기 강제 |
| `debate_gate.sh` | 토론모드 활성 시 GPT 직접 JS 조작 전 지침 읽기·debate_preflight 확인 차단 |
| `debate_independent_gate.sh` | 토론모드 활성 시 독립 견해 없이 GPT 응답 전송 차단 |
| `navigate_gate.sh` | 토론모드 활성 시 ChatGPT 직접 navigate 차단 (debate_mode 맥락 외 navigate는 통과) |
| `skill_instruction_gate.sh` | 인라인 python MES/ZDM 접근 시 SKILL.md 읽기 강제 |
| `skill_drift_check.sh` | 스킬 실행 시 최신 SKILL.md 읽기 드리프트 차단 |
| `debate_verify.sh` | 토론 합의 서명 검증 (`[3way]` 태그 커밋 무결성) |
| `permissions_sanity.sh` | settings.local.json 1회용 permissions 패턴·중복 탐지 advisory |
| `write_router_gate.sh` | 신규 파일 위치 화이트리스트 라우팅 gate — 4-Layer(루트/도메인/임시/시스템). advisory↔gate 모드 토글 (세션123 신설) |
| `auto_compile.sh` | 파일 수정 후 자동 컴파일/변환 |
| `write_marker.sh` | 파일 변경 마커 생성, 상태문서 수정 시 삭제 |
| `mode_c_log.sh` | C 트리거 커밋 후 .claude/state/mode_c_log.jsonl 기록 advisory (세션118 별건 3번 신설) |
| `share_after_push.sh` | git push 직후 share-result 필요 advisory 알림 (debate_20260429_103117_3way Phase B, advisory only, 자동 호출 금지) |
| `evidence_mark_read.sh` | 문서 읽기/갱신 → .ok 증거 마커 적립 |
| `gpt_followup_post.sh` | GPT 읽기/전송/후속작업 감지 → pending flag 관리 |
| `handoff_archive.sh` | HANDOFF.md 갱신 시 이전 세션 기록 아카이브 |
| `debate_send_gate_mark.sh` | 토론모드 활성 시 GPT 응답 읽기 후 send_gate 마커 갱신 |
| `post_commit_notify.sh` | git push 성공 시 Slack 자동 알림 발송 (event: PostToolUse) |
| `notify_slack.sh` | Slack 채널 알림 발송 |
| `stop_guard.sh` | 금지 문구 포함 시 Stop 차단 |
| `gpt_followup_stop.sh` | GPT pending flag 존재 시 Stop 차단 |
| `completion_gate.sh` | TASKS/HANDOFF 미갱신 시 Stop 차단 |
| `evidence_stop_guard.sh` | 증거 없는 실패/완료 결론 차단 |
| `auto_commit_state.sh` | 하이브리드 자동 커밋 (세션101) — 상태문서 AUTO 커밋+푸시, 나머지 리마인더 |


<!-- AUTO_HOOKS_END -->

### Commands (.claude/commands/)

| 커맨드 | subagent 역할 |
|--------|-------------|
| /doc-check | 문서 정합성 검사 (TASKS/STATUS/HANDOFF 충돌) |
| /task-status-sync | 상태 충돌 탐지 (패턴 A~D) |
| /review-claude-md | CLAUDE.md 규칙 검토 |

### 하네스 3인 체제

| 역할 | 담당 |
|------|------|
| Planner | 작업 범위와 기준 정리 |
| Generator | 기준에 따라 결과물 생성/수정 |
| Evaluator | 결과물을 기준표에 따라 판정 |

---

## 5. 실행 계층

반복 업무 자동화 스킬 + 스크립트.

<!-- AUTO_SKILLS_START -->

### Skills (90_공통기준/스킬/) — 20개 등록

> 이 섹션은 `generate_agents_guide.sh`가 자동 갱신. 수동 편집 시 덮어쓰기됨.

| 스킬 | Grade | 설명 |
|------|-------|------|
| assembly-cost-settlement | B | - |
| auto-fix | - | - |
| chomul-module-partno | A | 초물표 모듈품번(RSP) 일괄 반영 스킬. 초물표 xls 파일의 공용품번 박스에 모듈품번을 입력/수정하고,  |
| d0-production-plan | B | - |
| daily-routine | A | - |
| flow-chat-analysis | C | - |
| line-batch-mainsub | A | - |
| line-batch-management | A | - |
| line-batch-outer-main | A | - |
| line-mapping-validator | B | - |
| night-scan-compare | B | MES 야간스캔실적 조회 → BI 대비 비교 엑셀 자동 생성 |
| pptx-generator | B | - |
| production-report | B | 생산실적 집계 자동화 — BI 실적 + 임률단가 + 조립비 API → 생산관리 마스터리스트 자동 생성 |
| production-result-upload | A | - |
| skill-creator-merged | B | - |
| sp3-production-plan | B | SP3 생산계획 자동화 — ERP 계획 반영, D+1/D+2 생산계획 산출, 야간 이월 처리, 수동서열 반영 |
| supanova-deploy | A | - |
| token-threshold-warn | advisory | - |
| youtube-analysis | C | - |
| zdm-daily-inspection | A | ZDM 시스템 일상점검 자동 입력 (SP3M3 라인) |


<!-- AUTO_SKILLS_END -->

### 스킬 메타데이터 표준 (향후 업데이트 시 적용)

모든 SKILL.md frontmatter에 아래 필드 포함:
- `name`: 스킬 이름
- `description`: 1줄 설명 (트리거 조건 포함)
- `version`: 버전 (예: v9)
- `trigger`: 사용자가 어떤 말을 했을 때 활성화되는지
- `author`: 작성자
- `last_updated`: 최종 수정일

---

## 6. 감시 계층

외부 파일 변경 감지 → 자동 커밋/상태갱신/알림 체인.

> 실파일은 `90_공통기준/업무관리/` 하위에 존재하나, 스케줄러 등록/상시 운영 여부는 미확인.

| Phase | 스크립트 | 역할 | 운영 상태 |
|-------|---------|------|----------|
| 1 | watch_changes.py | 파일 변경 감지 (watchdog) + debounce 30분 | 실파일 존재, 운영 미확인 |
| 2 | commit_docs.py | allowlist 기준 git add/commit/push | 실파일 존재, 운영 미확인 |
| 3 | update_status_tasks.py | STATUS.md/TASKS.md 자동 갱신 | 실파일 존재, 운영 미확인 |
| 4 | slack_notify.py | Slack 알림 발송 | 실파일 존재, 운영 미확인 |
| 5 | notion_sync.py | Notion 현황판 동기화 | 실파일 존재, 운영 미확인 |
| 6 | skill_install.py | .skill 파일 변경 시 자동 설치 | 실파일 존재, 운영 미확인 |

---

## 실행 순서 플로우

```
[세션 시작]
  ├→ TASKS.md → STATUS.md → HANDOFF.md 읽기
  ├→ /doc-check subagent 실행 (필수)
  ├→ /task-status-sync subagent 실행 (필수)
  ├→ FAIL 있으면 즉시 수정
  └→ 작업 착수

[작업 실행]
  ├→ Plan-First: research.md → plan.md 승인 → 구현
  ├→ hooks 자동 검증 (PreToolUse 보호, PostToolUse 로그)
  └→ git commit 시 정합성 리마인드 (hook)

[작업 완료]
  ├→ TASKS.md 완료 항목 추가
  ├→ HANDOFF.md 세션 변경사항 기록
  ├→ Git 커밋/push
  ├→ GPT 공동작업방 결과 공유 (보고 아닌 공유)
  └→ Slack 알림 (필요 시)

[세션 종료]
  └→ HANDOFF.md 다음 AI 할 일 정리
```

## 장애 대응 절차

| 장애 | 증상 | 대응 |
|------|------|------|
| watch_changes.py 사망 | Slack AutoBot 알림 없음, .watch.lock에 죽은 PID | 헬스체크 스케줄러가 5분 내 자동 재시작. 수동: lock 삭제 후 VBS 런처 실행 |
| auto-commit 실패 | Slack에 [Git 커밋 실패] 알림 | watch_errors_*.log 확인 → 브랜치/allowlist/경로 문제 진단 |
| STATUS/TASKS 충돌 | doc-check FAIL | 즉시 수정. TASKS.md가 원본 (판정 우선순위) |
| hooks 미동작 | hook_log.txt에 기록 없음 | settings.local.json hooks 섹션 확인 → 스크립트 실행 권한 확인 |
| GPT 응답 없음 | ChatGPT 채팅방 로딩 실패 | 브라우저 새로고침 → 프로젝트방 첫 번째 대화 재진입 |
| Slack 발송 실패 | slack_errors_*.log에 에러 | Bot Token 만료 확인 → token_env_fallback_path .env 파일 확인 |

## 세션 시작 체크리스트

1. TASKS.md 읽기 (상태 원본)
2. STATUS.md 읽기 (재개 위치)
3. HANDOFF.md 읽기 (세션 메모)
4. `/doc-check` 실행 (정합성 검사 — **필수**)
5. `/task-status-sync` 실행 (상태 충돌 탐지 — **필수**)
6. FAIL 있으면 즉시 수정
7. 현업 질문이면 `업무_마스터리스트.xlsx` 먼저
