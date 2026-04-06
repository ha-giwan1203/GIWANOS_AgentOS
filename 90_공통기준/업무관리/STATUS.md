# 업무리스트 전체 운영 현황

> **이 파일은 운영 요약·재개 위치·주의사항 전용이다.**
> 작업 완료/미완료 상태의 원본은 TASKS.md이다. 이 파일에 상태를 독립 선언하지 않는다.

최종 업데이트: 2026-04-04 — 8단계 자동 루틴 강제 + completion_gate 버그 수정 (상세: TASKS.md 참조)

---

## 현재 운영 상태

| 항목 | 내용 |
|------|------|
| 현재 브랜치 | `main` (origin/main 동기화) |
| 활성 작업 원본 | `90_공통기준/업무관리/TASKS.md` |
| 미완료 작업 수 | TASKS.md 참조 |
| 자동화 파이프라인 | Phase 1~6 운영 중 (skill_install 포함) |
| hooks 체계 | 21개 등록, 14개 실발화 실증, jq 완전 제거, cp949 인코딩 수정 완료 |

---

## 현재 재개 위치

| 도메인 | 재개 위치 | 참조 |
|--------|---------|------|
| ~~라인배치 OUTER~~ | ~~runOuterLine(295)~~ — **사용자 취소** (2026-03-31) | `10_라인배치/STATUS.md` 참조 |
| 조립비정산 | 파이프라인 정상 운영 중 | `05_생산실적/조립비정산/CLAUDE.md` |
| subagent 확장 | 구현 완료 (GPT PASS 7bae2a78) | `_플랜/plan_subagent_expansion.md` |
| Fast/Full Lane | 규칙 확정 (GPT PASS 15b06459), 체크리스트 순차 작성 예정 | `.claude/rules/fast-full-lane.md` |
| 기능 활용 | 합의 완료 (GPT PASS), /sp3-verify 보류 (자연어 대체) | `.claude/rules/feature-utilization.md` |
| domain_guard | v3 phase guard 구현 완료 (토론모드 3단, GPT 합의 2턴) | `.claude/hooks/domain_guard.sh` |
| PPT 자동 생성 | 실무 투입 최종 PASS — 실데이터+육안검수 5/5 완료 | `90_공통기준/스킬/pptx-generator/SKILL.md` |
| GPT 지침 Git 관리 | 구현 완료 (GPT PASS 4bcd7877) | `90_공통기준/업무관리/gpt-instructions.md` |

---

## 자동화 파이프라인 상태

| Phase | 스크립트 | 상태 |
|-------|---------|------|
| Phase 1 | `watch_changes.py` | 운영 중 (작업 스케줄러 등록) |
| Phase 2 | `commit_docs.py` | 운영 중 |
| Phase 3 | `update_status_tasks.py` | 운영 중 |
| Phase 4 | `slack_notify.py` | 운영 중 (Token 갱신 완료) |
| Phase 5 | `notion_sync.py` | 운영 중 (per-page dedup 적용) |
| Phase 6 | `skill_install.py` | 운영 중 (.skill 변경 시 자동 압축 해제) |

---

## 주요 경로 기준

| 역할 | 경로 |
|------|------|
| 조립비 정산 파이프라인 실행 | `05_생산실적\조립비정산\03_정산자동화\run_settlement_pipeline.py` |
| BI 자동갱신 (스킬 내장) | `90_공통기준\스킬\production-result-upload\SKILL.md` 0단계 |
| 조립비 기준정보 | `05_생산실적\조립비정산\01_기준정보\기준정보_라인별정리_최종_V1_20260316.xlsx` |
| 스킬 패키지 위치 | `90_공통기준\스킬\` |
| 운영 지침 문서 | `90_공통기준\업무관리\` |
| 파일 감시 런처 | `90_공통기준\업무관리\watch_changes_launcher.vbs` |
| 스케줄러 등록 배치 | `90_공통기준\업무관리\register_watch_task.bat` |
| 마이그레이션 증적 | `98_아카이브\마이그레이션_20260328\` |

---

## 운영 주의사항

- 동기화 금지 구간: 매시 x0:10~13, x0:20~23, x0:30~33, x0:40~43, x0:50~53
- GitHub에 대용량 원본 엑셀 적재 금지
- 업무리스트 폴더 루트 임의 폴더 생성 금지
- Notion을 AI 작업 기준 저장소로 사용 금지
- 상태 판정은 TASKS.md 기준. STATUS/HANDOFF/Notion이 충돌하면 TASKS.md가 우선
- settings.local.json 토큰 하드코딩 금지 (2026-04-01 OAuth 토큰 제거)
- hooks 수정 후 반드시 smoke_test.sh 실행 (10케이스)
- 토론모드 금지 문구는 stop_guard.sh가 deterministic 차단

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
| 2026-04-06 13:54 | modified | step6_검증.py | 정산 파이프라인 스크립트 수정 |
| 2026-04-06 13:01 | modified | step8_오류리스트.py | 정산 파이프라인 스크립트 수정 |
| 2026-04-06 13:01 | modified | step7_보고서.py | 정산 파이프라인 스크립트 수정 |
| 2026-04-06 13:01 | modified | run_settlement_pipeline.py | 정산 파이프라인 스크립트 수정 |
| 2026-04-06 12:42 | modified | CLAUDE.md | CLAUDE.md 운영 기준 수정 |
| 2026-04-06 12:13 | modified | test_missing_column.py | 정산 파이프라인 스크립트 수정 |
| 2026-04-06 12:13 | modified | test_normal.py | 정산 파이프라인 스크립트 수정 |
| 2026-04-06 12:13 | modified | test_unmatched_parts.py | 정산 파이프라인 스크립트 수정 |
| 2026-04-06 12:13 | modified | _test_helpers.py | 정산 파이프라인 스크립트 수정 |
| 2026-04-06 12:13 | modified | build_master.py | BI 자동화 스크립트 수정 |
| 2026-04-06 12:13 | modified | _apply_all_v3.py | 초물관리 스크립트 수정 |
| 2026-04-06 12:13 | modified | _patch_v4.py | 초물관리 스크립트 수정 |
| 2026-04-06 12:13 | modified | CLAUDE.md | CLAUDE.md 운영 기준 수정 |
| 2026-04-06 12:13 | modified | CLAUDE.md | CLAUDE.md 운영 기준 수정 |
| 2026-04-06 12:13 | modified | README.md | README.md 수정 |
| 2026-04-06 12:13 | modified | SKILL.md | 스킬 문서 갱신 |
| 2026-04-06 12:13 | modified | RUNBOOK.md | 스킬 문서 갱신 |
| 2026-04-06 12:13 | modified | supanova-deploy.skill | 스킬 패키지 갱신 |
| 2026-04-06 12:13 | modified | SKILL.md | 스킬 문서 갱신 |
| 2026-04-06 12:13 | modified | deploy_checklist.md | 스킬 문서 갱신 |
| 2026-04-06 12:13 | modified | eval_cases.md | 스킬 문서 갱신 |
| 2026-04-06 12:13 | modified | sp3-production-plan.skill | 스킬 패키지 갱신 |
| 2026-04-06 12:13 | modified | SKILL.md | 스킬 문서 갱신 |
| 2026-04-06 12:13 | modified | zdm-daily-inspection-v2.skill | 스킬 패키지 갱신 |
| 2026-04-06 12:13 | modified | SKILL.md | 스킬 문서 갱신 |
| 2026-04-06 12:13 | modified | production-report.skill | 스킬 패키지 갱신 |
| 2026-04-06 12:13 | modified | prompt_template.md | 스킬 문서 갱신 |
| 2026-04-06 12:13 | modified | zdm-daily-inspection-v3.skill | 스킬 패키지 갱신 |
| 2026-04-06 12:13 | modified | SKILL.md | 스킬 문서 갱신 |
| 2026-04-06 12:13 | modified | 스킬_SP3생산계획_운영절차_v3.0.md | 스킬 문서 갱신 |
