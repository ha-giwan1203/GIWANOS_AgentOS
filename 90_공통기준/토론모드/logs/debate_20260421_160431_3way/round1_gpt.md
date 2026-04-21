# Round 1 — GPT 본론 (2026-04-21 T16:04)

## 판정: 조건부 통과

## 선호안: B+'
- B안 변형: TASKS 최상단 10줄 복제 X, **Git 원본 고정 스냅샷 블록만 덮어쓰기**
- 근거: A안 Notion 포기 수준, C안 과함, D안 기존 자산 버림

## 4개 묶음 필수 조건
1. generated snapshot 블록 (SYNC_START/END marker)
2. Notion API `position.after_block` 전환 (현재 `append after`는 deprecated)
3. 페이지 제목은 **세션 경계에서만** 갱신 (매 커밋 X — 검색·즐겨찾기 악영향 방지)
4. 제목 실패도 검증 로그에 승격 (현재 best-effort로 조용히 묻힘 — "가짜 성공" 방지)

## 불확실점 판정
1. **대상 블록만 교체 가능**: SYNC_START/END marker 방식 안전. 현재 `append after`는 deprecated → `position.after_block` 필수
2. **제목 매 커밋 갱신 비추**: API 가능하지만 검색·즐겨찾기·식별성 악영향. 세션 경계만
3. **TASKS.md 최상단 10줄 복제 취약**: 프론트매터(YAML) 블록이 더 안정

## 추가 놓친 리스크
- 성공 판정 허술 (제목 실패가 동기화 전체 성공으로 위장)
- API 버전 드리프트 (Notion-Version 2022-06-28 + deprecated after 혼재)
- manual edit 충돌 (generated block 편집 금지 운영 필요)
