# /finish — 작업 완료 9단계 자동 루틴

> `/share-result` 확장 루틴의 alias/wrapper. 단, 4.5단계(Notion 동기화)는 share-result 위임 밖 독립 실행.
> [역사] GPT 합의 2026-04-04 — 최초 8단계 자동 루틴 강제 방안 (세션86 오후 2026-04-21 3자 토론으로 9단계 확장, 4.5 Notion 독립 신설. 이 문구는 원형 보존 목적)
> 세션86 3자 토론(2026-04-21) 3way 만장일치: 4.5단계 Notion 동기화를 `/finish` 전용으로 분리.

이 명령은 파일 변경이 포함된 작업 완료 시 9단계를 끊김 없이 실행한다. (세션86 3자 토론: 8→9단계, 4.5 Notion 신설)
내부적으로 `/share-result`의 확장 루틴을 따른다.

## finish_state.json 상태 추적

`90_공통기준/agent-control/state/finish_state.json`에 단계별 상태를 기록한다.

```json
{
  "terminal_state": "in_progress",
  "committed_pushed": false,
  "gpt_shared": false,
  "gpt_judgment": null,
  "user_reported": false,
  "followup_checked": false,
  "exception_reason": null
}
```

`terminal_state` 값: `in_progress` / `done` / `exception`
- `exception`일 때만 `exception_reason` 필수

## 실행 순서 (9단계 — 세션86 3자 토론 4.5 신설 반영)

### 1~3단계: 상태 문서 갱신
- TASKS.md 완료 이력 추가
- HANDOFF.md 세션 변경사항 갱신
- STATUS.md 재개 위치 갱신 (필요 시)

### 3.7단계: untracked 파일 체크 (GPT 합의 세션64)
- `git status --short | grep '^??'` 실행으로 untracked 파일 감지
- 감지된 각 파일에 대해 3분류:
  - **stage**: 현재 작업 산출물 → `git add`
  - **ignore**: `.gitignore` 또는 `.state`/일시 파일 → 무시 (사용자에게 1줄 보고)
  - **skip**: 판단 불가 → 사용자에게 목록 제시 후 판정 요청
- 목적: 파일이 작성만 되고 커밋 안 되어 세션 간 휘발되는 것 방지 (세션63 커맨드 4개 사례 재발 방지)

### 4단계: 커밋+푸시
- `bash .claude/hooks/final_check.sh --full --fix` 선행 (STATUS 드리프트 시 자동 갱신)
- `git add` → `git commit` → `git push`
- finish_state.json에 `committed_pushed: true` 기록

### 4.5단계: Notion 동기화 (세션86 3자 토론 채택 — Git 커밋+푸시 완료 후)
- 실행: `python 90_공통기준/업무관리/notion_sync.py --manual-sync || true`
- 동작: events 없이 STATUS 요약(update_summary) + 부모 페이지(sync_parent_page) 갱신. 허위 이력 append 없음.
- 배치: 페이지 ID 3개는 `90_공통기준/업무관리/notion_config.yaml` 참조
  - 부모: `331fee67-0be8-81fd-9bf7-d0c2af54bc07`
  - STATUS: `331fee67-0be8-81f7-9f15-c3aaabfbd94a`
  - TASKS: `331fee67-0be8-818c-b2bc-cd8da0a40db8`
- 실패 정책: soft-fail (`|| true`). `90_공통기준/agent-control/state/notion_sync_pending.flag` 생성 + 다음 단계 진행. 성공 시 flag 제거.
- 이 단계는 `/finish` 전용 — `/share-result` 단독 호출 경로에서는 실행되지 않는다 (책임 분리)

### 5단계: GPT 공유
- Chrome MCP로 GPT 토론방에 전송 (CDP 폐기됨)
- 입력 전 미확인 응답 점검 필수
- SHA + 수정 내용 + 판정 요청
- finish_state.json에 `gpt_shared: true` 기록

### 6단계: GPT 응답 대기 + 판정 확인
- 적응형 polling (5/10/15초)
- GPT 판정값 파싱 (우선순위):
  1. 명시 판정: PASS / 정합 / 부분반영 / 미반영 / 보류 / 기준미확인 / 임시검토 / FAIL
  2. fallback: FAIL/구조충돌 키워드 탐색
- finish_state.json에 `gpt_judgment: "{판정값}"` 기록

### 7단계: 사용자 보고
- GPT에 공유한 내용 + GPT 판정 결과를 함께 1회 보고
- 하네스 분석이 있었으면 1줄 요약 포함
- finish_state.json에 `user_reported: true` 기록

### 8단계: GPT 후속 의견 1회 재확인
- GPT 마지막 응답에 추가 수정 요구가 있는지 확인
- FAIL/구조충돌 → 수정 루프 재진입 (terminal_state 유지: in_progress)
- 개선 제안 → 다음 의제로 기록, terminal_state → done
- 후속 없음 → terminal_state → done
- finish_state.json에 `followup_checked: true`, `terminal_state: "done"` 기록

### 예외 처리
- timeout/로그인만료/네트워크오류 → `terminal_state: "exception"`, `exception_reason` 기록
- 예외 시에도 사용자 보고는 수행

## 공유 범위
- **모든 커밋은 예외 없이 GPT에 공유한다** — 상태 문서 갱신(6단계) 후 추가 커밋이 발생하면 해당 커밋도 GPT에 공유한 뒤 사용자 보고한다
- 커밋 종류(docs, fix, feat 등)에 따라 공유를 임의 생략하지 않는다

## Stop guard 연동
- completion_gate.sh가 finish_state.json의 terminal_state를 확인
- `terminal_state != "done" && != "exception"`이면 종료 차단
- dirty.flag와는 별도 체크 (상태 의미 분리)
