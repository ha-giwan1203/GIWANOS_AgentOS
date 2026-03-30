# 업무리스트 작업 목록

최종 업데이트: 2026-03-30 (작업 스케줄러 등록 완료 + notion-sync 수정 완료)

---

## 진행 중

없음

---

## 대기 중 (우선순위 순)

### [중] 상태 원본 단일화 설계
- TASKS/STATUS/HANDOFF/Notion이 같은 상태를 각자 보유하는 구조 → 정합성 문제 반복 원인
- 설계: TASKS 단일 원본화 + 파생 문서 자동 생성/동기화 방향 GPT와 상의
- 적용 전 GPT 검토 필수



### [완료] 하네스 파일럿 1회차 검증 — 2026-03-30
- Generator FAIL / Evaluator PASS 94점 — Known Exception 오판정 방지 효과 확인
- 결과 조립비정산 STATUS.md에 기록 완료

### [완료] Step 6 FAIL 2레벨 분리 — 2026-03-30 이전
- KNOWN_EXCEPTIONS 레지스트리, `chk()` severity 파라미터 적용
- overall 3단계 (FAIL/WARNING/PASS) 분리 완료
- HANDOFF.md에 기록됨

### [완료] skill-creator 3단계 절차 연결 — 2026-03-30
- `skill-creator-merged.skill` SKILL.md에 `harness` 모드 추가 (모드 테이블 + 규칙 + 3단계 섹션)
- Stage 1 Planner / Stage 2 Generator / Stage 3 Evaluator 절차 명문화
- 평가 기준표: `하네스_스킬평가기준표.md` 연결, PASS/CONDITIONAL/FAIL/BLOCKED 판정 포함
- 컨텍스트 분리 원칙 및 피드백 루프 (최대 3회) 포함

### [낮] 루트 CLAUDE.md 하네스 원칙 승격 (보류)
- 조건: 파일럿 검증 2회 이상 완료 후 검토
- 현재: 루트 수정 금지

### [완료] 작업 스케줄러 등록 — 2026-03-30
- `업무리스트_WatchChanges` 태스크 로그온 트리거 등록 완료
- watch_changes.py Python 직접 실행 방식 (VBS 우회)
- PID 15588 정상 실행 확인

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
