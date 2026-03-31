# research: Notion 본문 동기화 문제

작성일: 2026-03-31
문제: notion_sync.py가 변경 이력만 append하고 본문(STATUS/TASKS 요약)은 갱신하지 않음

---

## 1. 현재 구조

- `sync_status_page()` → `_append_blocks()` (append만)
- `sync_tasks_page()` → `_append_blocks()` (append만)
- 본문 교체 함수 없음

## 2. 해결 방향 비교

| 방식 | 장점 | 단점 |
|------|------|------|
| MCP update_content (old_str/new_str) | 즉시 가능, 코드 수정 최소 | 테이블 블록 매칭 어려움 |
| Notion raw API block_id 업데이트 | 정확한 블록 제어 | notion_sync.py 대폭 수정, API 복잡 |
| 요약 텍스트 블록 교체 | 매칭 쉬움, 안전 | 기존 테이블은 수동 정리 필요 |

## 3. 채택: 요약 텍스트 블록 교체 (1단계)

- Notion 페이지 상단에 `<!-- SYNC_SUMMARY -->` 마커가 포함된 텍스트 블록 배치
- sync 시 이 블록만 찾아서 TASKS.md 파싱 결과로 교체
- 기존 테이블/이력은 건드리지 않음
- GPT 의견(block_id)은 2단계 장기 과제로 유보

## 4. 구현 범위

notion_sync.py에 `_update_summary()` 함수 추가:
1. TASKS.md 읽기 → 진행 중/대기 중/완료 수 파싱
2. Notion 페이지에서 요약 블록 찾기
3. 요약 블록 내용 교체
4. 실패 시 기존 append 동작 유지 (안전장치)
