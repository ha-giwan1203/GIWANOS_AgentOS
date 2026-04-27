# 업무리스트 전체 운영 현황

> **이 파일은 운영 요약·재개 위치·주의사항 전용이다.**
> 작업 완료/미완료 상태의 원본은 TASKS.md이다. 이 파일에 상태를 독립 선언하지 않는다.
> 도메인 하위 `STATUS.md`와 `TASKS.md`는 도메인 내부 메모로만 사용한다. 전역 상태 우선순위는 `업무관리/TASKS.md` 기준이다.

최종 업데이트: 2026-04-27 — 세션118 (수동 갱신: publish_worktree_to_main.sh main stale 자동 감지 + --auto-sync 옵트인, HANDOFF 1번 강제 처리 + dry-run 위치 보정 fix-up)

---

## 현재 운영 상태

| 항목 | 내용 |
|------|------|
| 현재 브랜치 | `main` |
| 활성 작업 원본 | `90_공통기준/업무관리/TASKS.md` |
| 미완료 작업 수 | TASKS.md 참조 |
| 자동화 체계 | **Claude hooks 일원화** (2026-04-11). 백그라운드 프로세스 체인(watch_changes→auto_commit→slack→notion) 폐기, Windows 스케줄러 제거 |
| hooks 체계 | **활성 수 기준축: `bash .claude/hooks/list_active_hooks.sh --count` (Single Source, 세션93 2자 토론 합의 / 세션107 수동 카운트 표기 제거)**. 스킬 19개. 세션101 auto_commit_state.sh 신설 (Stop 5번째, 하이브리드 자동 커밋: 상태문서 AUTO, 나머지 MANUAL 리마인더). 세션93 hook_registry.sh legacy 격하. 세션91 final_check statusLine 버그 수정. 세션76 commit_gate push 단독 final_check 스킵 근본 해결. 세션74 쟁점 G 실물 분리. 세션72 Phase 2-B: 핵심 훅 6종 exit 2 전환 + completion_gate 소프트 블록 + timing 배선. |

---

## 현재 재개 위치

| 도메인 | 재개 위치 | 참조 |
|--------|---------|------|
| ~~라인배치 OUTER~~ | ~~runOuterLine(295)~~ — **사용자 취소** (2026-03-31) | `10_라인배치/STATUS.md` 참조 |
| 조립비정산 | 파이프라인 정상 운영 중 | `05_생산실적/조립비정산/CLAUDE.md` |
| subagent 확장 | 구현 완료 (GPT PASS 7bae2a78) | `_플랜/plan_subagent_expansion.md` |
| Fast/Full Lane | 규칙 확정 (GPT PASS 15b06459). 규칙은 `data-and-files.md`로 통합됨 | `.claude/rules/data-and-files.md` |
| 기능 활용 | 합의 완료 (GPT PASS). 별도 규칙 파일 폐기, CLAUDE.md 본문으로 흡수 | `CLAUDE.md` |
| domain_guard | v3 구현 후 폐기 → _archive 이동. risk_profile_prompt로 대체 | `.claude/hooks/_archive/domain_guard.sh` |
| evidence hook | 증거기반 위험실행 차단기 5개 구현 (GPT 부분반영) | `.claude/hooks/evidence_*.sh` |
| 토론모드/게이트 보정 | **현재 정책: chrome-devtools-mcp(CDP) 단독** (세션105 전환, 세션107 L-3 정합). 세션32 Chrome MCP 단일화 → 세션105 CDP 전환으로 갱신됨. send_gate→mcp_send_gate 교체, harness_gate 유지. idle composer 오탐 제거, completion gate 축소, 한국어-only, final_check settings 기준 재정렬 | `90_공통기준/토론모드/`, `.claude/hooks/` |
| 토론모드 보류 안건 | → TASKS.md "진행중 / 보류" 참조 | `90_공통기준/업무관리/TASKS.md` |
| GPT 전송 스킬 | /gpt-send, /gpt-read 실사용 PASS (세션36) | `.claude/commands/gpt-send.md` |
| verify_xlsm | 1차 구조 검증 10/10 PASS, 2차 COM 불필요(결과 시트) | `90_공통기준/agent-control/verifiers/verify_xlsm.py` |
| Notion 부모 페이지 | Integration 연결 + sync_parent_page() 정상 동작 (세션36) | `90_공통기준/업무관리/notion_sync.py` |
| PPT 자동 생성 | 실무 투입 최종 PASS — 실데이터+육안검수 5/5 완료 | `90_공통기준/스킬/pptx-generator/SKILL.md` |
| GPT 지침 Git 관리 | 구현 완료 (GPT PASS 4bcd7877) | `90_공통기준/업무관리/gpt-instructions.md` |

---

## 자동화 체계 (2026-04-11 훅 일원화 전환)

| 기능 | 이전 (폐기) | 현재 |
|------|------------|------|
| 파일 감시 | `watch_changes.py` + Windows 스케줄러 | 폐기 (SPOF — 크래시 시 자동복구 불가) |
| 자동 커밋 | `commit_docs.py` (watch_changes 호출) | 폐기 (hooks 내 completion_gate로 대체) |
| 상태 갱신 | `update_status_tasks.py` | 폐기 (Edit 도구로 직접 갱신) |
| Slack 알림 | `slack_notify.py` (watch_changes 호출) | `notify_slack.sh` Notification hook → `slack_notify.py` |
| Notion 동기화 | `notion_sync.py` (watch_changes 호출) | `/finish` 3.5단계 → MCP `notion-update-page` |
| 스킬 설치 | `skill_install.py` | 유지 (.skill 변경 시 자동 압축 해제) |

---

## 주요 경로 기준

| 역할 | 경로 |
|------|------|
| 조립비 정산 파이프라인 실행 | `05_생산실적\조립비정산\03_정산자동화\run_settlement_pipeline.py` |
| BI 자동갱신 (스킬 내장) | `90_공통기준\스킬\production-result-upload\SKILL.md` 0단계 |
| 조립비 기준정보 | `05_생산실적\조립비정산\01_기준정보\기준정보_라인별정리_최종_V1_20260316.xlsx` |
| 스킬 패키지 위치 | `90_공통기준\스킬\` |
| 운영 지침 문서 | `90_공통기준\업무관리\` |
| ~~파일 감시 런처~~ | ~~`90_공통기준\업무관리\watch_changes_launcher.vbs`~~ (폐기 — 훅 일원화) |
| ~~스케줄러 등록 배치~~ | ~~`90_공통기준\업무관리\register_watch_task.bat`~~ (폐기 — 훅 일원화) |
| 마이그레이션 증적 | `98_아카이브\마이그레이션_20260328\` |

---

## 운영 주의사항

- 동기화 금지 구간: 매시 x0:10~13, x0:20~23, x0:30~33, x0:40~43, x0:50~53
- GitHub에 대용량 원본 엑셀 적재 금지
- 업무리스트 폴더 루트 임의 폴더 생성 금지
- Notion을 AI 작업 기준 저장소로 사용 금지
- 상태 판정은 TASKS.md 기준. STATUS/HANDOFF/Notion이 충돌하면 TASKS.md가 우선
- settings.local.json 토큰 하드코딩 금지 (2026-04-01 OAuth 토큰 제거)
- hooks 수정 후 반드시 smoke_test.sh 실행 (102케이스, 세션14 기준)
- 토론모드 금지 문구는 stop_guard.sh가 deterministic 차단
- Windows PowerShell 세션에서 Bash가 필요하면 `.claude/scripts/run_git_bash.ps1 '<command>'` 또는 `C:\Program Files\Git\bin\bash.exe -lc '<command>'`를 사용한다

---

## GPT 검증 결과 자동반영 규칙

GPT 검증 결과를 기록할 때 아래 표준 문장만 사용한다.

### TASKS.md 완료 이력용
- `검증 PASS — {대상} 반영 실물 확인`
- `검증 조건부 PASS — {대상} 핵심 반영 확인, 부수 정합성 {N}건 후속 수정`
- `검증 FAIL — {대상} 설명과 실물 불일치, 재검토 필요`

### HANDOFF.md 공동작업 상태용
- `GPT 검증: {sha} PASS`
- `GPT 검증: {sha} 조건부 PASS ({사유})`
- `GPT 검증: {sha} FAIL ({사유})`

### 위치 규칙
- PASS/조건부 PASS/FAIL은 **HANDOFF에만 현재형**으로 남긴다
- 완료 이력은 **TASKS에만 누적**한다
- STATUS.md에는 검증 상태를 새로 선언하지 않는다 — "TASKS/HANDOFF 참조" 유지

---

## 완료 이력 참조

완료된 작업 전체 목록은 `TASKS.md`의 "## 완료됨" 섹션 참조.
Git 이력: `git log --oneline` 또는 GitHub `ha-giwan1203/GIWANOS_AgentOS`

## 자동 감지 변경 이력
| 시각 | 이벤트 | 파일 | 변경 내용 |
|------|--------|------|----------|
| 2026-04-06 18:42 | modified | CLAUDE.md | CLAUDE.md 운영 기준 수정 |
| 2026-04-06 18:41 | modified | verify_master_from_gerp.py | 정산 파이프라인 스크립트 수정 |
| 2026-04-06 18:41 | modified | CLAUDE.md | CLAUDE.md 운영 기준 수정 |
| 2026-04-06 18:21 | modified | CLAUDE.md | CLAUDE.md 운영 기준 수정 |
| 2026-04-06 17:56 | modified | CLAUDE.md | CLAUDE.md 운영 기준 수정 |
| 2026-04-06 17:46 | modified | step4_기준정보매칭.py | 정산 파이프라인 스크립트 수정 |
| 2026-04-06 17:25 | moved    | verify_master_from_gerp.py | 정산 파이프라인 스크립트 수정 |
| 2026-04-06 17:22 | modified | CLAUDE.md | CLAUDE.md 운영 기준 수정 |
| 2026-04-06 17:22 | modified | _pipeline_config.py | 정산 파이프라인 스크립트 수정 |
| 2026-04-06 17:22 | modified | CLAUDE.md | CLAUDE.md 운영 기준 수정 |
| 2026-04-06 16:23 | modified | CLAUDE.md | CLAUDE.md 운영 기준 수정 |
| 2026-04-06 16:16 | modified | CLAUDE.md | CLAUDE.md 운영 기준 수정 |
| 2026-04-06 16:14 | modified | CLAUDE.md | CLAUDE.md 운영 기준 수정 |
| 2026-04-06 16:14 | modified | CLAUDE.md | CLAUDE.md 운영 기준 수정 |
| 2026-04-06 16:12 | modified | build_formula_version.py | 정산 파이프라인 스크립트 수정 |
| 2026-04-06 15:54 | modified | SKILL.md | 스킬 문서 갱신 |
| 2026-04-06 15:27 | modified | step8_오류리스트.py | 정산 파이프라인 스크립트 수정 |
| 2026-04-06 15:27 | modified | step7_보고서.py | 정산 파이프라인 스크립트 수정 |
| 2026-04-06 15:27 | modified | step5_정산계산.py | 정산 파이프라인 스크립트 수정 |
| 2026-04-06 15:27 | modified | run_settlement_pipeline.py | 정산 파이프라인 스크립트 수정 |
| 2026-04-06 15:27 | modified | README.md | README.md 수정 |
| 2026-04-06 15:19 | modified | CLAUDE.md | CLAUDE.md 운영 기준 수정 |
| 2026-04-06 15:14 | modified | _test_helpers.py | 정산 파이프라인 스크립트 수정 |
| 2026-04-06 15:14 | modified | test_unmatched_parts.py | 정산 파이프라인 스크립트 수정 |
| 2026-04-06 15:14 | modified | test_normal.py | 정산 파이프라인 스크립트 수정 |
| 2026-04-06 15:14 | modified | test_missing_column.py | 정산 파이프라인 스크립트 수정 |
| 2026-04-06 15:14 | modified | step7_시각화입력생성.py | 정산 파이프라인 스크립트 수정 |
| 2026-04-06 15:14 | modified | step7_대시보드.py | 정산 파이프라인 스크립트 수정 |
| 2026-04-06 15:14 | modified | step7_slack_보고.py | 정산 파이프라인 스크립트 수정 |
| 2026-04-06 15:14 | modified | step6_검증.py | 정산 파이프라인 스크립트 수정 |
