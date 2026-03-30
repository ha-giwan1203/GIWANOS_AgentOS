# 업무리스트 작업 목록

> **이 파일은 AI 작업 상태의 유일한 원본이다.**
> 완료/미완료/진행중/차단 상태는 이 파일에만 기록한다.
> STATUS.md·HANDOFF.md·Notion은 이 파일을 참조하며, 독립적으로 상태를 선언하지 않는다.
> 판정 우선순위: TASKS.md > STATUS.md > HANDOFF.md > Notion
>
> **주의: 이 파일은 현업 업무 전체 목록의 원본이 아니다.**
> 실제 업무 일정, 남은 과제, 반복 업무, 마감일의 기준 원본은 `90_공통기준/업무관리/업무_마스터리스트.xlsx`이다.
> 이 파일은 그중 AI가 수행해야 하는 자동화·문서화·구조 개편·검토·인수인계 작업만 관리한다.

최종 업데이트: 2026-03-30 (상태 원본 단일화 규칙 적용 — GPT+Claude 설계 합의)

---

## 진행 중

없음

---

## 대기 중 (우선순위 순)

### [중] 조립비 정산 step7 시각화 자동화 도입
- 목적: 조립비 정산 파이프라인의 step7 보고서 단계에 Visualization 스킬을 연결해 HTML 대시보드 + PNG 보고 이미지를 자동 생성
- 기준 원본: `05_생산실적/조립비정산/`
- 적용 범위: 월간 조립비 정산 결과 요약, 라인별 금액 비교, 전월 대비 증감, 이상치/누락 표시, 3줄 인사이트
- 출력 목표: HTML 1장 (`월간_조립비_대시보드.html`) + PNG 1장 + Slack 보고용 이미지
- 구현 원칙: 계산/검증은 기존 정산 파이프라인(step1~6) 유지, Visualization은 step7 출력 전용
- 선행 조건: step7 요약 데이터 구조 확정, 라인명/금액/전월비교/이상치 판정 기준 고정, 시범 1회 생성 후 GPT PASS
- 완료 기준: 월 1회 실행 가능한 HTML + PNG 자동 생성, Slack 또는 보고서 삽입 재사용 가능
- 참조: Visualization 스킬 (커리어해커 알렉스 영상 분석 기반, 2026-03-30)

**진행 현황 (2026-03-30)**
- [완료] step7_시각화입력생성.py 작성 + 실데이터 검증
  - 출력: `_cache/step7_visualization_input.json`
  - 검증: total_cost=179,180,199원 / 10라인 / anomaly=1건(SP3M3 Known WARNING) / 합계 일치
- [완료] step7_대시보드.py + templates/step7_dashboard.html.j2 작성 + 실행 검증
  - HTML + PNG 생성 확인 (Playwright headless shell)
  - 구성: Jinja2 템플릿 / Chart.js CDN / Playwright PNG
  - 출력: `_cache/월간_조립비_대시보드.html` + `_cache/월간_조립비_대시보드.png`
- [완료] watch_changes.py Phase 6 훅 추가 (skill_install.py) + .skill 확장자 감시 등록
- [대기] GPT PASS 확인 후 TASKS.md DONE 전환
- [다음] Slack 보고 이미지 연결 (3차)

### [낮] 루트 CLAUDE.md 하네스 원칙 승격 (보류)
- 조건: 파일럿 검증 2회 이상 완료 후 검토
- 현재 1회 완료

### [낮] 도메인 STATUS.md 점검
- `05_생산실적\조립비정산\STATUS.md` — 마이그레이션 이후 경로 반영 확인
- `10_라인배치\STATUS.md` — 현행 기준 반영 확인

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
