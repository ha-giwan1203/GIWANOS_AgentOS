# Plan: Claude Code Hooks 도입 (하이브리드 전환)

작성일: 2026-03-31
승인 상태: [x] GPT 조건부 승인 (구현 진행 가능, 최종 PASS는 실물 기준)

---

## 목표
세션 내부 자동화 6건을 hooks 이벤트 기반으로 전환. 기존 watch_changes.py는 세션 외부 상시 감시 역할로 유지.

## 비목표
- watch_changes.py 전면 교체
- 새로운 외부 감시 도구 도입
- Agent Teams / Swarm Mode 도입

---

## 구현 계획 (승인 후에만 구현 시작)

### Step 1 — SessionStart 훅 추가
- settings.json에 SessionStart 이벤트 등록
- 세션 시작 시 "TASKS.md → STATUS.md → HANDOFF.md 읽기 순서 리마인드" 메시지 출력
<!-- [수정금지] 기존 permissions 구조 변경 금지 -->
**세부 작업:**
- [ ] .claude/hooks/ 디렉토리 생성
- [ ] session_start.sh 스크립트 작성 (리마인드 메시지 출력)
- [ ] settings.local.json에 hooks.SessionStart 추가

### Step 2 — PreToolUse(Bash) 위험 명령 차단 훅
- rm -rf, git reset --hard 등 파괴적 명령 사전 차단
**세부 작업:**
- [ ] block_dangerous.sh 스크립트 작성
- [ ] settings.local.json에 hooks.PreToolUse matcher=Bash 추가

### Step 3 — Notification 훅 (Slack 알림 연동)
- Claude Code 알림 발생 시 기존 slack_notify.py 자동 호출
**세부 작업:**
- [ ] notify_slack.sh 래퍼 스크립트 작성
- [ ] settings.local.json에 hooks.Notification 추가

### Step 4 — ConfigChange 훅 (.skill 변경 감지)
- ConfigChange(source=skills) 이벤트로 스킬 변경 감지 (GPT 수정: FileChanged → ConfigChange, 오발동 방지)
<!-- [GPT수정] FileChanged는 basename 기준 감시라 .skill 오발동 여지 큼. ConfigChange가 정석 -->
**세부 작업:**
- [ ] skill_config_change.sh 스크립트 작성
- [ ] settings.local.json에 hooks.ConfigChange 추가

### Step 4-1 — InstructionsLoaded 훅 (CLAUDE.md 로드 관측)
- CLAUDE.md 또는 .claude/rules/*.md 로드 시 로그 기록 (GPT 추가 권고: 값싸고 효과 큼)
**세부 작업:**
- [ ] instructions_loaded.sh 스크립트 작성
- [ ] settings.local.json에 hooks.InstructionsLoaded 추가

### Step 5 — SessionEnd 훅 (HANDOFF 리마인드)
- 세션 종료 시 "HANDOFF.md 갱신했는지 확인" 리마인드
**세부 작업:**
- [ ] session_end.sh 스크립트 작성
- [ ] settings.local.json에 hooks.SessionEnd 추가

### Step 6 — 검증 및 문서화
- 전체 hooks 동작 테스트
- CLAUDE.md에 hooks 운영 규칙 한 줄 추가
- TASKS.md 완료 처리
**세부 작업:**
- [ ] 각 hook 트리거 테스트
- [ ] 기존 watcher와 충돌 없음 확인
- [ ] 문서 갱신 + 커밋/푸시

---

## 제약사항

- 기존 watch_changes.py 코드 수정 금지 (하이브리드 공존)
- settings.local.json의 기존 permissions 구조 변경 금지
- hooks 스크립트는 .claude/hooks/ 디렉토리에 집중 배치
- Windows 환경 호환성 필수 (bash 스크립트는 Git Bash 기준)

---

## 진행 상태

- [x] research.md 완성 — GO
- [x] plan.md GPT 조건부 승인
- [x] 구현 (settings.local.json + 스크립트 6건, PreToolUse 제거)
- [ ] 검증 (다음 세션 /hooks 증빙)
- [x] 운영상 완료 (Git 반영 커밋 e3d1cb06, ea7baece)

---

## 재개 위치

- 현재 단계: **운영상 완료**, 검증 증적만 다음 세션에서 남기면 최종 PASS
- 다음: Phase 4 (도메인 STATUS.md 점검 + 정산 파이프라인 확인)
