# Round 1 — Claude 종합·설계안 (6-5)

- 작성 시각: 2026-04-21 10:50 KST
- 전제: 6-2 Gemini→GPT "동의"(단서 없음) + 6-4 GPT→Gemini "동의"(단서 없음), 양측 합의율 높음
- issue_class: **B** (구조 변경 — finish.md 실행 흐름 수정) → round_count=1이지만 skip_65=false 유지
- claude_delta: **partial** (양측 공통분모 + Claude 실물 검증 신규 반영)

## 양측 공통 채택 (실증됨 4건)

1. **B안 기반**: finish.md 3.5단계를 share-result 위임 밖으로 분리. share-result는 GPT 공유 전용.
2. **41세션 소급 포기**: 현재 스냅샷(세션86 시점)만 정방향 덮어쓰기.
3. **실패 non-blocking**: soft-fail + 다음 단계 진행.
4. **smoke_test 신설**: finish.md에 `notion_sync.py` 호출 구문 존재 검증.

## Gemini 신규 + Claude 채택 (1건)

5. **Git 커밋 완료 후 동기화**: Git 원본주의 보호. Notion은 Git 뒤에 따라가는 보조 채널.

## Claude 실물 검증 기반 신규 제안 (2건)

### 6. finish.md 3.5단계 → **4.5단계로 재번호**
- 현 명세: 3.5(Notion) → 4(커밋+푸시) 순서 — **Git 전에 Notion 동기화**하는 오류 있음
- 수정: Notion 동기화는 **4단계(커밋+푸시) 직후**인 **4.5단계**로 이동
- 근거: Gemini 지적("push 전 동기화 시 정합성 깨짐") + finish.md L35-39 실물 확인
- 영향: B안 실행 흐름 자체가 Gemini 지적을 구현하려면 재번호 필수

### 7. "MCP notion-update-page" → **`notion_sync.py` 직접 호출**로 교체
- 현 명세 (finish.md:38): `MCP notion-update-page 도구 사용`
- 수정: `bash: python 90_공통기준/업무관리/notion_sync.py`
- 근거: 
  - notion_sync.py 815줄 완성 구현 존재 (토큰 관리·배치·에러처리 일관)
  - MCP 호출은 세션별 MCP 연결 상태 의존 — 환경 의존성 ↑
  - 스크립트 호출은 cron/hook 재사용 가능 (DRY)

## 보류 (후속 별건)

- GPT "토큰·페이지ID·finish_state.json 기록 경로 보강" — 지적 내용 구체 불명, notion_config.yaml·finish_state.json 스키마 교차 검증 후 별건 TASKS로.

## 실행 계획 (채택 시)

### 파일 수정 3건

**파일 1**: `.claude/commands/finish.md`
- L28 "8단계" → "9단계" (섹션 추가로 단계 증가)
- L35-39 Notion 블록 삭제 (3.5단계 제거)
- L49~ "4단계: 커밋+푸시" 직후에 신규 "4.5단계: Notion 동기화" 추가
  - 내용: `python 90_공통기준/업무관리/notion_sync.py` 실행
  - 실패 시 `90_공통기준/agent-control/state/notion_sync_pending.flag` 생성 + 다음 단계 진행
  - 성공 시 flag 제거
- 단계 번호 재조정

**파일 2**: `.claude/commands/share-result.md`
- 신규 경고 주석 1줄 추가: "Notion 동기화는 `/finish` 4.5단계 전용. 여기서 처리하지 않음."

**파일 3**: `.claude/hooks/smoke_test.sh`
- 신규 섹션 추가 (맨 끝): "=== N. finish.md Notion 동기화 구문 존재 ==="
  - `grep -q "notion_sync.py" .claude/commands/finish.md` 검증
  - 실패 시 FAIL

### 실측 동기화 1회 실행

- `python 90_공통기준/업무관리/notion_sync.py` 수동 실행으로 세션86 시점 스냅샷 복구
- 3개 페이지(부모·STATUS·TASKS) 현행화 확인

### pending flag 처리 훅

- SessionStart 훅에 notion_sync_pending.flag 감지 시 재시도 로직 (별건 TASKS 유지 — 이번 의제 범위 밖)

## pass_ratio 예상 판정
- 6-2 동의 + 6-4 동의 + 양측 웹 UI 최종판정 대기 = 예상 3/3 (양측 완전합의)
- 단, Claude 신규 제안 2건(4.5 재번호, MCP→스크립트 교체)은 양측 재검증 필요
