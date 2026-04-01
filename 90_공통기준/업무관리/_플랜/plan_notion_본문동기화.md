# Plan: Notion 본문 동기화 1단계

작성일: 2026-04-01
상태: 구현 진행 중
GPT 합의: 채택 (5건 요구사항 전부 수용)

---

## 원본 기준 (필수 명시)

**본문 생성 원본은 TASKS.md가 1순위**이다.
STATUS.md와 HANDOFF.md는 보조 요약이다.
Notion이 상태 원본처럼 보이게 만들면 안 된다.

---

## 1단계 범위 (고정)

요약 텍스트 블록 교체만 한다.

### 허용
- Notion STATUS 페이지 "요약" 헤딩 아래 bullet 블록 내용 교체
- TASKS.md 파싱 → 진행 중/대기 중/완료 수 + 항목명 + 차단사유

### 금지
- 데이터베이스 스키마 변경
- 속성 추가
- 페이지 구조 이동
- 뷰 수정
- 테이블 블록 수정 (기존 테이블은 수동 정리)

---

## 재실행 안전성 (멱등성)

- append가 아니라 **replace** 방식
- 같은 내용을 두 번 실행해도 블록 중복 추가 안 됨
- `_update_summary_blocks()`가 기존 bullet block을 PATCH로 교체
- 새 블록을 생성하지 않음 (기존 블록 ID 재사용)

---

## 검증 절차

1. **반영 전**: 각 bullet block 현재 내용 읽기 (before 스냅샷)
2. **반영 후**: PATCH 결과를 after 스냅샷으로 기록
3. **1:1 대조**: before vs after 비교하여 변경/동일 판정
4. **로그 파일**: `notion_sync_verify_YYYYMMDD.log`에 기록

---

## 즉시 중단 조건 (실패 시 롤백 기준)

| 조건 | 동작 |
|------|------|
| 페이지 못 찾음 (blocks 빈 목록) | 즉시 중단, False 반환 |
| 요약 블록 매칭 실패 (content_blocks 없음) | 즉시 중단, False 반환 |
| 부분 갱신 (일부 블록만 성공) | 즉시 중단, 에러 로그 + False 반환 |

어설프게 반쯤 바뀐 상태를 방지한다.

---

## 구현 현황

| 항목 | 상태 | 커밋 |
|------|------|------|
| _parse_tasks_summary 상세화 | ✅ 완료 | 7059dc6e |
| _build_summary_lines 신규 | ✅ 완료 | 7059dc6e |
| _update_summary_blocks 스냅샷 | ✅ 완료 | 7059dc6e |
| update_summary 즉시 중단 3조건 | ✅ 완료 | 7059dc6e |
| 검증 로그 파일 생성 | ✅ 완료 | 7059dc6e |
| 부모 페이지 링크 허브 단순화 | ✅ 완료 (GPT 합의 2번 확정) | Notion MCP 직접 반영 |
