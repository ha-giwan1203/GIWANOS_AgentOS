# 별건 기록 — GPT 시스템 감사 분석 (Notion 의제 직전 대화 맥락)

- 수신 시각: 2026-04-21 이전 (세션86 Notion 토론 진입 직전 대화)
- 채팅방: `69e6d13f-6aec-83e8-91a6-842943a7c6eb` (현재 3자 토론 대화방과 동일 스레드)
- 주제: 저장소 전체 구조 감사 — hooks·settings·토론모드 드리프트
- 현재 상태: **미해결 후속 질문 있음** ("우선순위 5개 잘라드릴까요?")

## 핵심 지적 (GPT 원문 요약 — 하네스 이전 보존용)

### 좋은 축 3개 (채택 가능)
- TASKS.md 단일 상태 원본 고정 → 판정 기준 일관
- settings.json(팀) / settings.local.json(로컬) 분리 방향
- 토론모드 캡슐화 (CLAUDE + gpt-send/read + gate + 로그)

### 문제 축 4개 (후속 안건)
1. **hooks README 드리프트** — settings.json PreToolUse에 `skill_drift_check.sh`, `debate_verify.sh`, `permissions_sanity.sh` 등록됐으나 hooks README "활성 Hook 표"에서 누락
2. **훅 숫자 불일치** — 전역 STATUS "32개" vs settings.json + hooks README 실활성 "31개"
3. **settings.local.json 절대경로 잔존** — `C:/Users/User/Desktop/업무리스트/...` 환경 의존성, 팀/개인 분리 취지 훼손
4. **completion_gate 역할·분류 불일치** — 실제는 Stop 차단 gate인데 분류표는 measurement로 적힘

### 토론모드 과대 복잡화 경고
- 스킬이 아니라 작은 워크플로 엔진 수준 (CLAUDE.md + gpt-send.md + gpt-read.md + 복수 gate + send/read 마커)
- 작은 드리프트가 즉시 장애로 전이

### evidence_gate 후속 관찰
- 방향은 맞으나 req/ok 마커·session_start_restore 의존성 높음

## 후속 처리 계획

- 이 문서는 로그 디렉터리에 보존 (3자 토론 스레드와 같은 대화방이라 맥락 섞임 방지용)
- TASKS.md "별건 후속 안건" 섹션에 "시스템 감사 4개 축 드리프트 보정" 항목 추가
- 우선순위 5개 잘라달라는 GPT 후속 질문은 Notion 의제 종결 후 재요청
- 판정 라벨은 아직 없음 — 감사 결과물이라 Claude 실물 검증 후 채택·보류·버림 분류 필요

## Claude 실물 검증 전 유의
- "훅 32 vs 31" 숫자는 settings.json + hooks README 각각 카운트 직접 검증 필수
- "completion_gate measurement 오분류"는 hooks README 해당 행 원문 확인 필수
- "settings.local.json 절대경로 잔존"은 파일 grep 직접 확인 필수
