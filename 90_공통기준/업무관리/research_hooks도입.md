# Research: Claude Code Hooks 도입 (하이브리드 전환)

작성일: 2026-03-31
작성: Claude (GPT 공동작업)
판정: GO

---

## 1. 작업 식별

- 목적: Claude Code 세션 내부 자동화를 hooks 이벤트 기반으로 전환
- 범위: 기존 watch_changes.py(외부 상시 감시)는 유지, 세션 내부 자동화만 hooks로 이동
- GPT 판정: "전면 교체가 아닌 하이브리드 전환이 맞다"

---

## 2. 현재 구조

### watch_changes.py 책임 목록
1. 파일 변경 감지 (watchdog Observer, 30분 idle debounce)
2. 변경 이벤트 JSONL 로그 기록
3. Phase 2: flush 후 commit_docs.process_events() 자동 호출
4. Phase 6: .skill 파일 변경 시 자동 설치 (skill_install.py)
5. 중복 실행 방지 (PID lock 파일)
6. Windows 작업 스케줄러 ONLOGON 등록으로 상시 실행

### settings.local.json 현황
- hooks 설정: **없음** (permissions만 존재, 129행)
- 현재 permissions: python 실행, git, powershell, 각종 스크립트 허용 규칙

### 도메인 STATUS.md 불일치 (GPT 지적)
- 라인배치 STATUS.md에 "다음 재개: runOuterLine(295)" 남아있으나 사용자가 "OUTER 재개 취소" 지시
- → Phase 4 도메인 STATUS.md 점검에서 정리 예정

---

## 3. Hooks 이벤트 구조 (공식 문서 기준)

### 사용 가능 이벤트 (22종)
- SessionStart / SessionEnd — 세션 시작/종료
- UserPromptSubmit — 프롬프트 제출 시
- PreToolUse / PostToolUse / PostToolUseFailure — 도구 호출 전/후
- PermissionRequest — 권한 요청 시
- Notification — 알림 발생 시
- SubagentStart / SubagentStop — 서브에이전트 시작/종료
- TaskCreated / TaskCompleted — 작업 생성/완료
- Stop / StopFailure — 응답 완료/실패
- InstructionsLoaded — CLAUDE.md 로드 시
- ConfigChange — 설정 변경 시
- CwdChanged — 작업 디렉토리 변경 시
- FileChanged — 감시 파일 변경 시 (matcher로 파일명 지정)
- WorktreeCreate / WorktreeRemove — 워크트리 생성/제거
- PreCompact / PostCompact — 컨텍스트 압축 전/후
- Elicitation / ElicitationResult — MCP 사용자 입력 요청/응답

### 설정 형식 (settings.json)
```json
{
  "hooks": {
    "이벤트명": [
      {
        "matcher": "도구명 또는 파일패턴",
        "hooks": [
          {
            "type": "command",
            "command": "스크립트경로"
          }
        ]
      }
    ]
  }
}
```

### Hook 유형 3가지
1. command — 셸 명령 실행 (stdin으로 JSON 입력)
2. http — HTTP POST 엔드포인트 호출
3. prompt — LLM 프롬프트 실행 (Claude가 직접 처리)

---

## 4. Hooks로 옮길 수 있는 책임 vs 못 옮기는 책임

### Hooks로 이동 가능
1. **SessionStart**: 세션 시작 시 TASKS.md/STATUS.md 자동 읽기 알림
2. **PostToolUse(Write/Edit)**: 파일 수정 후 자동 git add + 변경 로그 기록
3. **Notification**: Slack 알림 자동 발송 (기존 slack_notify.py 연동)
4. **SessionEnd**: 세션 종료 시 HANDOFF.md 갱신 리마인드
5. **FileChanged**: .skill 파일 변경 시 자동 설치 (기존 Phase 6 대체)
6. **PreToolUse(Bash)**: 위험 명령 차단 (rm -rf 등)

### Hooks로 이동 불가 (watcher 유지)
1. **상시 파일 감시**: Claude Code 세션이 꺼져있을 때의 파일 변경 감지
2. **30분 debounce 배치 처리**: 세션 외부에서 누적 변경 일괄 처리
3. **Windows 작업 스케줄러 연동**: ONLOGON 상시 실행
4. **commit_docs.py 자동 호출**: 세션 없이도 주기적 git 커밋

---

## 5. 하이브리드 전환 후 watcher 잔존 책임

- watch_changes.py: 세션 외부 상시 감시 + debounce + commit_docs 자동 호출 유지
- hooks: 세션 내부 이벤트 기반 자동화 (실시간, 결정론적)
- 중복 방지: hooks가 처리한 이벤트는 watcher가 재처리하지 않도록 로그 기반 중복 제거

---

## 6. Research 판정 체크리스트

- [x] 기존 구조 (watch_changes.py) 책임 목록 파악
- [x] hooks 이벤트 22종 확인
- [x] 이동 가능/불가 책임 분리
- [x] settings.json 설정 형식 확인
- [x] 하이브리드 전환 후 watcher 잔존 책임 명시
- [x] STATUS.md 불일치 기록 (GPT 지적)

**판정: GO** — plan.md 작성 진행 가능
