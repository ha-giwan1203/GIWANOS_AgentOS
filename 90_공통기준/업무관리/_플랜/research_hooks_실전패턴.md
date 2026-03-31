# research: Claude Code Hooks 실전 패턴 분석

작성일: 2026-03-31
출처: A등급 1번 리소스 (Hooks 실전 워크플로우)

---

## 1. 현재 상태

- `.claude/hooks/` 디렉토리에 스크립트 존재 (이전 세션에서 생성)
- `settings.local.json`에 hooks 섹션 없음 — 비활성 상태
- watch_changes.py(Phase 1~5) 자동화 체인이 대체 역할 수행 중

## 2. Hooks 아키텍처 요약 (외부 리소스 기반)

### 핵심 이벤트 5종

| 이벤트 | 시점 | 용도 | 차단 가능 |
|--------|------|------|----------|
| PreToolUse | 도구 실행 전 | 보안 게이트, 파일 보호, 위험 명령 차단 | O (exit 2) |
| PostToolUse | 도구 실행 후 | 자동 포맷, 검증, 린팅 | X |
| Notification | 알림 발송 시 | Slack/외부 알림 연동 | X |
| Stop | 응답 완료 시 | 상태 갱신, 로그 기록 | X |
| SubagentStop | 서브에이전트 완료 시 | 하위 에이전트 결과 처리 | X |

### settings.json 설정 구조

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{
        "type": "command",
        "command": "bash .claude/hooks/block-unsafe.sh"
      }]
    }],
    "PostToolUse": [{
      "matcher": "Write|Edit",
      "hooks": [{
        "type": "command",
        "command": "bash .claude/hooks/validate.sh"
      }]
    }]
  }
}
```

### exit code 규칙
- `0`: 정상 통과
- `2`: Blocking error — 작업 차단 + Claude에 이유 전달

## 3. 우리 프로젝트 적용 포인트

### 적용 O (watch_changes.py 보완)

| 패턴 | hook 이벤트 | 용도 |
|------|------------|------|
| 보호 파일 편집 차단 | PreToolUse (Write/Edit) | TASKS.md, 기준정보 엑셀 등 직접 수정 방지 |
| 위험 git 명령 차단 | PreToolUse (Bash) | force push, reset --hard 차단 |
| 파일 수정 후 자동 검증 | PostToolUse (Write/Edit) | CLAUDE.md 규칙 위반 검사 |
| 세션 종료 시 상태 갱신 | Stop | HANDOFF.md 자동 갱신 알림 |
| 완료 알림 | Notification | Slack 발송 연동 |

### 적용 X (watch_changes.py 대체 불가)

| 기능 | 이유 |
|------|------|
| 파일 감시 (watchdog) | hooks는 Claude 세션 내에서만 동작, 외부 파일 변경 감지 불가 |
| debounce + 배치 처리 | hooks는 즉시 실행, 30분 idle 대기 패턴 없음 |
| Phase 3~5 (STATUS/TASKS/Notion/Slack 체인) | hooks 단독으로 체인 오케스트레이션 불가 |

## 4. 제안: 하이브리드 구조

```
[Claude 세션 내 작업]
  → Hooks (PreToolUse/PostToolUse/Stop)
  → 즉시 검증, 차단, 알림

[외부 파일 변경 감지]
  → watch_changes.py (Phase 1~5)
  → debounce → commit → STATUS/TASKS → Slack → Notion
```

두 체계가 서로 다른 영역을 담당. 대체가 아닌 보완 관계.

## 5. 다음 단계

1. `.claude/hooks/` 기존 스크립트 점검 — 재활용 가능 여부
2. settings.local.json에 hooks 최소 3건 등록 (PreToolUse 보호, PostToolUse 검증, Notification)
3. GPT 승인 후 plan 작성 → 적용

---

Sources:
- InfoGrab: Claude Code /loop, Hooks, Auto memory 점검 자동화
- PixelMojo: Claude Code Hooks 12 Events + Production Patterns
- Claude Code 공식 문서: hooks-guide
