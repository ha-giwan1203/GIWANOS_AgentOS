# notion_sync.py 가이드

## 동작 위치

Phase 1 → Phase 3 → Phase 2 → Phase 4 → **Phase 5 (Notion 동기화)**

Phase 3가 STATUS.md / TASKS.md를 갱신하면 자동으로 Notion 페이지에도 반영.

---

## 초기 설정 (1회만)

Notion 페이지에 통합 앱 연결이 필요합니다.

1. **Notion에서 `📁 업무리스트 운영` 페이지** 열기
2. 우상단 `...` 클릭 → **연결 (Connections)** → **연결 추가**
3. `GPT 자동 분류 시스템` 검색 → 선택
4. 하위 페이지(STATUS / TASKS)에 자동으로 권한 상속됨

> 이 작업을 하지 않으면 Python 스크립트에서 `HTTP 404` 오류가 발생하고,
> 동기화는 건너뜀 (나머지 Phase 1~4 흐름에는 영향 없음)

---

## 동기화 내용

### STATUS 페이지 (`📊 STATUS — 전체 운영 현황`)
- `🔄 자동 감지 변경 이력` 섹션 자동 생성 + 배치 이벤트 append
- 항목: 타임스탬프, 배치 ID, 핵심 파일 변경, STATUS/TASKS 갱신, Git 커밋 결과

### TASKS 페이지 (`✅ TASKS — 작업 목록`)
- `🤖 자동 생성 태스크` 섹션 자동 생성 + `[auto]` 항목 append
- Phase 3가 TASKS.md에 [auto] 항목 추가 시에만 동작

---

## 동기화 조건

| 조건 | 설정 키 | 기본값 |
|------|---------|--------|
| Phase 3 STATUS/TASKS 갱신 성공 | `sync_on.status_tasks_updated` | true |
| 핵심 파일 변경 포함 배치 | `sync_on.critical_file_changed` | true |

---

## 토큰 설정

- 통합 앱: **GPT 자동 분류 시스템**
- 토큰: `C:/Users/User/Desktop/gpt설정api/.env` → `NOTION_TOKEN=ntn_...`
- 또는 환경변수 `NOTION_TOKEN`

---

## 실행 방법

### dry-run (실제 동기화 없이 콘솔 출력)
```bash
python notion_sync.py --dry-run
```

### 수동 동기화 테스트
```bash
python notion_sync.py --batch-id "manual-test"
```

### watch_changes.py 기동 시 자동 연결
```bash
python watch_changes.py
```

---

## 메시지 예시 (Notion STATUS 페이지)

```
🔄 자동 감지 변경 이력

[2026-03-28 14:35] 배치 a1b2c3d4 | 파일 2건
• 핵심 파일 변경: CLAUDE.md
• STATUS/TASKS 갱신: STATUS.md, TASKS.md
• Git 커밋 2건 (abc1234)
```

---

## 중복 방지

- `batch_id` 기반 dedup
- `dedup_window_hours: 1` — 동일 배치 1시간 이내 재동기화 없음
- 상태 파일: `.notion_dedup_state.json`
