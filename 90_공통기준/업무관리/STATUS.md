# 업무리스트 전체 운영 현황

> **이 파일은 운영 요약·재개 위치·주의사항 전용이다.**
> 작업 완료/미완료 상태의 원본은 TASKS.md이다. 이 파일에 상태를 독립 선언하지 않는다.

최종 업데이트: 2026-03-31 (auto_commit_config 수정, Hooks 실전 패턴 적용, 멀티에이전트 research)

---

## 현재 운영 상태

| 항목 | 내용 |
|------|------|
| 현재 브랜치 | `main` (origin/main 동기화) |
| 활성 작업 원본 | `90_공통기준/업무관리/TASKS.md` |
| 미완료 작업 수 | TASKS.md 참조 |
| 자동화 파이프라인 | Phase 1~5 운영 중 |

---

## 현재 재개 위치

| 도메인 | 재개 위치 | 참조 |
|--------|---------|------|
| ~~라인배치 OUTER~~ | ~~runOuterLine(295)~~ — **사용자 취소** (2026-03-31) | `10_라인배치/STATUS.md` 참조 |
| 조립비정산 | 파이프라인 정상 운영 중 | `05_생산실적/조립비정산/CLAUDE.md` |

---

## 자동화 파이프라인 상태

| Phase | 스크립트 | 상태 |
|-------|---------|------|
| Phase 1 | `watch_changes.py` | 운영 중 (작업 스케줄러 등록) |
| Phase 2 | `commit_docs.py` | 운영 중 |
| Phase 3 | `update_status_tasks.py` | 운영 중 |
| Phase 4 | `slack_notify.py` | 운영 중 (Token 갱신 완료) |
| Phase 5 | `notion_sync.py` | 운영 중 (per-page dedup 적용) |

---

## 주요 경로 기준

| 역할 | 경로 |
|------|------|
| 조립비 정산 파이프라인 실행 | `05_생산실적\조립비정산\03_정산자동화\run_settlement_pipeline.py` |
| BI 자동복사 배치 | `05_생산실적\_자동화\bi_copy.bat` |
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

---

## 완료 이력 참조

완료된 작업 전체 목록은 `TASKS.md`의 "## 완료됨" 섹션 참조.
Git 이력: `git log --oneline` 또는 GitHub `ha-giwan1203/GIWANOS_AgentOS`

## 자동 감지 변경 이력
| 시각 | 이벤트 | 파일 | 변경 내용 |
|------|--------|------|----------|
| 2026-03-31 13:44 | modified | 스킬_SP3생산계획_변경이력_v3.0.md | 스킬 문서 갱신 |
| 2026-03-31 13:35 | modified | build_master.py | BI 자동화 스크립트 수정 |
| 2026-03-31 13:35 | modified | bi_scheduler.bat | BI 자동화 배치 파일 수정 |
| 2026-03-31 13:35 | modified | bi_copy.bat | BI 자동화 배치 파일 수정 |
| 2026-03-31 13:35 | modified | 스킬_SP3생산계획_자동화규칙_v3.0.md | 스킬 문서 갱신 |
| 2026-03-31 13:33 | modified | 스킬_SP3생산계획_운영절차_v3.0.md | 스킬 문서 갱신 |
| 2026-03-31 13:32 | modified | zdm-daily-inspection-v3.skill | 스킬 패키지 갱신 |
| 2026-03-31 13:32 | modified | youtube-analysis.skill | 스킬 패키지 갱신 |
| 2026-03-31 13:32 | modified | supanova-deploy.skill | 스킬 패키지 갱신 |
| 2026-03-31 13:32 | modified | skill-creator-merged.skill | 스킬 패키지 갱신 |
| 2026-03-31 13:32 | modified | mes-production-upload.skill | 스킬 패키지 갱신 |
| 2026-03-31 13:32 | modified | line-mapping-validator.skill | 스킬 패키지 갱신 |
| 2026-03-31 13:32 | modified | line-batch-outer-main.skill | 스킬 패키지 갱신 |
| 2026-03-31 13:32 | modified | line-batch-management.skill | 스킬 패키지 갱신 |
| 2026-03-31 13:32 | modified | line-batch-mainsub.skill | 스킬 패키지 갱신 |
| 2026-03-31 13:32 | modified | debate-mode.skill | 스킬 패키지 갱신 |
| 2026-03-31 13:32 | modified | chomul-module-partno.skill | 스킬 패키지 갱신 |
| 2026-03-31 13:32 | modified | assembly-cost-settlement.skill | 스킬 패키지 갱신 |
| 2026-03-31 13:32 | modified | adversarial-review.skill | 스킬 패키지 갱신 |
| 2026-03-31 09:26 | modified | CLAUDE.md | CLAUDE.md 운영 기준 수정 |
| 2026-03-31 09:26 | modified | CLAUDE.md | CLAUDE.md 운영 기준 수정 |
| 2026-03-31 08:46 | modified | 운영지침_커넥터관리_v1.0.md | 운영 지침 문서 수정 |
| 2026-03-31 08:46 | modified | 운영핵심파일_보호목록_v1.0.md | 보호 파일 목록 수정 |
| 2026-03-31 08:46 | modified | CLAUDE.md | CLAUDE.md 운영 기준 수정 |
| 2026-03-31 07:40 | modified | skill-creator-merged.skill | 스킬 패키지 갱신 |
| 2026-03-31 07:21 | modified | CLAUDE.md | CLAUDE.md 운영 기준 수정 |
| 2026-03-31 07:12 | modified | CLAUDE.md | CLAUDE.md 운영 기준 수정 |
| 2026-03-31 07:12 | modified | CLAUDE.md | CLAUDE.md 운영 기준 수정 |
| 2026-03-31 07:01 | modified | CLAUDE.md | CLAUDE.md 운영 기준 수정 |
| 2026-03-31 04:56 | modified | CLAUDE.md | CLAUDE.md 운영 기준 수정 |
