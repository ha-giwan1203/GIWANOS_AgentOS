# 업무리스트 작업 목록

> **이 파일은 AI 작업 상태의 유일한 원본이다.**
> 완료/미완료/진행중/차단 상태는 이 파일에만 기록한다.
> STATUS.md·HANDOFF.md·Notion은 이 파일을 참조하며, 독립적으로 상태를 선언하지 않는다.
> 판정 우선순위: TASKS.md > STATUS.md > HANDOFF.md > Notion
>
> **주의: 이 파일은 현업 업무 전체 목록의 원본이 아니다.**
> 실제 업무 일정, 남은 과제, 반복 업무, 마감일의 기준 원본은 `90_공통기준/업무관리/업무_마스터리스트.xlsx`이다.
> 이 파일은 그중 AI가 수행해야 하는 자동화·문서화·구조 개편·검토·인수인계 작업만 관리한다.

최종 업데이트: 2026-03-31 (auto_commit_config branch/push 오기입 수정 — 자동화 체인 복구, GPT PASS)

---

## 진행 중

없음

---

## 대기 중 (우선순위 순)
### [auto] 정산 파이프라인 실행 테스트 확인 — **차단: 4월 데이터 대기**
- 출처: `step7_대시보드.py` 변경 감지
- 자동 생성 항목 — 4월 GERP/구ERP 실적 데이터 입수 후 자동 확인 예정
- 현 시점 강제 실행 불필요 (3월 데이터 기준 파이프라인 정상 동작 확인됨)




### ~~[낮] 루트 CLAUDE.md 하네스 원칙 승격~~ → 완료됨

### ~~[낮] 도메인 STATUS.md 점검~~ → 완료됨 (2026-03-31)
- 조립비정산 STATUS.md: 정합성 OK
- 라인배치 STATUS.md: OUTER 재개 취소 반영 (커밋 833a675b)

---

## 완료됨

| 항목 | 완료일 |
|------|--------|
| 폴더 마이그레이션 Phase 0~7 | 2026-03-28 |
| 파일 정리 1차 (94건 아카이브) | 2026-03-28 |
| 커넥터 운영 지침 v1.0 확정 | 2026-03-28 |
| 보호 파일 10건 목록 고정 | 2026-03-28 |
| 보류 파일 5건 최종 판정 | 2026-03-28 |
| CLAUDE.md 전면 개정 (1차) | 2026-03-28 |
| __pycache__ 삭제 | 2026-03-28 |
| Notion 업무 현황 페이지 생성 | 2026-03-28 |
| Slack 완료 보고 발송 | 2026-03-28 |
| Google Calendar 후속 작업 4건 등록 | 2026-03-28 |
| GitHub 운영 문서 push (PR #8) | 2026-03-28 |
| GitHub PR #8 머지 (main 반영) | 2026-03-28 |
| 자동화 동기화 Phase 1 (watch_changes.py) | 2026-03-28 |
| 자동화 동기화 Phase 2 (commit_docs.py) | 2026-03-28 |
| 자동화 동기화 Phase 3 (update_status_tasks.py) | 2026-03-28 |
| 자동화 동기화 Phase 4 (slack_notify.py) | 2026-03-28 |
| Slack 채널 연결 테스트 (MCP 경유) | 2026-03-28 |
| watch_changes.py Startup 폴더 상시 실행 등록 | 2026-03-28 |
| 작업 스케줄러 등록 파일 작성 (bat/xml) | 2026-03-28 |
| 폴더 생성 규칙 메모리 저장 | 2026-03-28 |
| 커넥터 운영구조 재정의 (Drive/GitHub/Notion 역할 확정) | 2026-03-28 |
| CLAUDE.md 2차 개정 (파일명규칙·환경설정 삭제, AI 인수인계 추가) | 2026-03-28 |
| 운영지침_커넥터관리_v1.0.md v1.1 갱신 | 2026-03-28 |
| README.md 신규 생성 (루트 AI 세션 진입점) | 2026-03-28 |
| HANDOFF.md 신규 생성 (AI 인수인계 문서 체계) | 2026-03-28 |
| GitHub PR #9 생성 및 main 머지 | 2026-03-28 |
| 조립비정산 데이터사전 동기화 (데이터사전 v1.0 + pipeline_contract.md + CLAUDE.md) | 2026-03-28 |
| line-batch-management.skill 패키지화 (v7→v9 기준 전환, SNAP-ON/LASER MARKING 갱신) | 2026-03-28 |
| ENDPART라인배정 파일 용도 확인 — 임시 참고자료 확정 (갱신 기준 불필요) | 2026-03-28 |
| MCP context7 설치 (`@upstash/context7-mcp`) | 2026-03-30 |
| MCP sequential-thinking 설치 (`@modelcontextprotocol/server-sequential-thinking`) | 2026-03-30 |
| mcp_설치현황.md 신규 생성 (전체 MCP 목록·프롬프트 문서화) | 2026-03-30 |
| youtube-analysis 스킬 제작 (URL → 자막 자동 추출 + 분석) | 2026-03-30 |
| YouTube_영상분석.md 프롬프트 신규 생성 | 2026-03-30 |
| 하네스 엔지니어링 파일럿 도입 (조립비정산 Evaluator + 운영가이드 + 스킬평가기준표) | 2026-03-30 |
| Slack Bot Token 갱신 완료 — slack_notify.py 발송 성공, slack_config.yaml 경로 수정 | 2026-03-28 |
| Slack 멘션 추가 — build_message + --message 경로 두 곳 mention_user_id 적용, 폰 알림 정상화 | 2026-03-28 |
| 파일 정리 2차 확인 — 99_임시수집 비어있음, 추가 작업 없음 | 2026-03-28 |
| 작업 스케줄러 등록 (업무리스트_WatchChanges 로그온 트리거) | 2026-03-30 |
| Step 6 FAIL 2레벨 분리 (KNOWN_EXCEPTIONS/severity/overall 3단계) | 2026-03-30 |
| skill-creator 3단계 절차 연결 (harness 모드, Planner/Generator/Evaluator) | 2026-03-30 |
| 하네스 파일럿 1회차 검증 (Generator FAIL / Evaluator PASS 94점) | 2026-03-30 |
| 상태 원본 단일화 설계 — TASKS 단일 원본, STATUS/HANDOFF 역할 재정의 | 2026-03-30 |
| 조립비 정산 step7 시각화 PoC — HTML 대시보드 + PNG 생성 (GPT PASS) | 2026-03-30 |
| watch_changes.py Phase 6 훅 — .skill 자동 설치 (skill_install.py) | 2026-03-30 |
| step7 Slack PNG 발송 — files:write 스코프 추가, Slack files v2 API 3단계 완성 | 2026-03-30 |
| Plan-First 워크플로우 도입 — CLAUDE.md 3개 규칙 + debate-mode.skill v2.4 + research/plan 템플릿 2종 | 2026-03-30 |
| 전체 폴더 정리 — 토론모드 중복 폴더 제거, debate-mode 언패킹 v2.4 동기화, _cache gitignore 추가 | 2026-03-31 |
| 하네스 파일럿 2회차 — skill-creator harness 모드 3가지 한계 해결 (평가기준참조/KnownException/피드백루프), Evaluator PASS 95점 | 2026-03-31 |
| 루트 CLAUDE.md 하네스 검증 원칙 승격 — 공통 4원칙(사용시점/3인체제/KnownException/피드백루프) GPT 공동작업 | 2026-03-31 |
| 루트 CLAUDE.md 공동작업 운영 원칙 5항목 추가 + 공동작업 표 금지 반영 | 2026-03-31 |
| Phase 1-1 Hooks 하이브리드 도입 — SessionStart/PreToolUse/Notification/ConfigChange/InstructionsLoaded/SessionEnd 6건, GPT 조건부 승인 | 2026-03-31 |
| 도메인 STATUS.md 점검 완료 — 조립비정산 정합성 OK, 라인배치 OUTER 재개 취소 반영 | 2026-03-31 |
| 프로젝트 커맨드 3종 작성 — doc-check/task-status-sync/review-claude-md (.claude/commands/ + Git 미러링) | 2026-03-31 |
| auto_commit_config.yaml 오기입 수정 — branch: "업무리스트"→"main", push_on_commit: false→true (자동화 체인 복구) | 2026-03-31 |
| Hooks 실전 패턴 적용 — PreToolUse 보호 2계층, PostToolUse 로그, Notification 스팸방지 (GPT 승인) | 2026-03-31 |
