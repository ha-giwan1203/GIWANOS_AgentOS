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

### Hooks (.claude/hooks/) — 5개 활성 (settings.json+settings.local.json 기준)

> 상세: `.claude/hooks/README.md` 참조. 아카이브: `.claude/hooks/_archive/`
> 이 섹션은 `generate_agents_guide.sh`가 자동 갱신. 수동 편집 시 덮어쓰기됨.

| 스크립트 | 역할 |
|---------|------|


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

### Skills (90_공통기준/스킬/) — 21개 등록

> 이 섹션은 `generate_agents_guide.sh`가 자동 갱신. 수동 편집 시 덮어쓰기됨.

| 스킬 | Grade | 설명 |
|------|-------|------|
| assembly-cost-settlement | B | 월말 조립비 정산 자동화 — 대원테크(0109) 10개 라인 GERP/구ERP 합계 + 차이 유형 분류 +  |
| auto-fix | - | - |
| chomul-module-partno | A | 초물표 모듈품번(RSP) 일괄 반영 — AB5:AJ14 박스에 RSP 입력/수정 + 라인코드 SP3S03→S |
| d0-production-plan | B | ERP D0 추가생산지시 자동화 (SP3M3 MAIN + SD9A01 OUTER). xlsm 추출 → ERP |
| daily-routine | A | ZDM 일상점검 + MES 생산실적 업로드 통합 자동화 (월~토 08:07 cron) |
| flow-chat-analysis | C | Flow.team SP3S03 채팅방 원문 → 품질·설비 이슈 자동 분류 + 월별 보고서 |
| jobsetup-auto | B | SmartMES 잡셋업 첫 서열 품번 자동 입력 (REST API v3.x). 17 검사항목/30초. 첫 서 |
| line-batch-mainsub | A | ERP 메인서브 라인배치 자동화 — SP3메인서브 품번 검색 + SUB ASSY 그리드 조립라인 자동 입력  |
| line-batch-management | A | ERP 라인배치 관리 통합 자동화 — SP3메인서브 + OUTER 라인 (검색 기반 + 리스트업 기반). 시 |
| line-batch-outer-main | A | ERP OUTER/MAIN 라인배치 자동화 — 검색 없이 그리드 행 순서대로 리스트업 처리 |
| line-mapping-validator | B | 품번-라인배정 정합성 검증 — 기준 품번 vs 라인배정(ERP/GERP) 비교 + A~F 판정 (일치/컬러확 |
| night-scan-compare | B | MES 야간스캔실적 조회 → BI 대비 비교 엑셀 자동 생성 (4시트 데이터+수식+양식) |
| pptx-generator | B | PPT 자동 생성 (템플릿 편집 + 신규 생성). python-pptx + matplotlib + Beaut |
| production-report | B | 생산실적 집계 자동화 — BI 실적 + 임률단가 + 조립비 API → 생산관리 마스터리스트 자동 생성 |
| production-result-upload | A | MES 생산실적 자동 업로드 — BI 엑셀 → SaveExcelData.do API 직접 POST. dail |
| skill-creator-merged | B | 재사용 스킬 제작·수정·평가·패키징 — 6 모드 (draft / improve / eval / optimiz |
| sp3-production-plan | B | SP3 생산계획 자동화 — ERP 계획 반영, D+1/D+2 산출, 야간 이월, 수동서열 반영 |
| supanova-deploy | A | Pinterest 레퍼런스 → Gemini 영상 → WebP 프레임 + 스크롤 애니메이션 → 템플릿 HTML |
| token-threshold-warn | advisory | 저장소 문서 비대화 사전 감시 — TASKS/HANDOFF/MEMORY/incident 라인·바이트 측정 + |
| youtube-analysis | C | YouTube 영상 분석 (자동 + 수동 모드). 자막+프레임 추출 → 9개 관점 분석 → A/B/C 판정  |
| zdm-daily-inspection | A | ZDM 일상점검 자동 입력 (SP3M3 19개 점검표 / 75개 항목). daily-routine 통합 또는 |


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
