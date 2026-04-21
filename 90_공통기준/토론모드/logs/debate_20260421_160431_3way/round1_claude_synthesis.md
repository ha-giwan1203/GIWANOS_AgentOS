# Round 1 — Claude 종합안 (2026-04-21 T16:04)

## 판정: 채택 (양측 동의 — GPT 조건부통과 + Gemini 통과, pass_ratio 예상 1.0)

## 최종 합의안: B+' (확장)

Notion 동기화 범위를 **"generated snapshot 블록 덮어쓰기" + "페이지 제목 세션경계 갱신"**으로 확장.

### 구현 7개 묶음

1. **SYNC_START/END marker 블록** (STATUS 페이지 상단에 고정 marker 설치, 그 안만 재생성)
2. **`position.after_block` API 전환** (현재 deprecated `after` → 최신 규격)
3. **페이지 제목: 세션 경계에서만 갱신** (매 커밋 X)
4. **제목 실패 검증 로그 승격** (best-effort 조용한 실패 제거, 부분 성공 명시)
5. **"편집 금지" 경고 헤더** (generated block 최상단에 수동 편집 금지 안내)
6. **TASKS.md 상단 YAML 프론트매터 블록** (세션/GitHub SHA/훅 수/smoke/최근 5세션 구조화)
7. **마커 수동 삭제 자동 재생성 fallback** (Gemini 추가 — marker 부재 시 STATUS 최상단에 재생성)

### 갱신 대상 핵심 지표 (snapshot 블록 내용)
- 최종 업데이트 (세션 번호 + 날짜)
- GitHub 동기화 (날짜 + commit SHA 최근)
- 훅 시스템 (raw/활성 수)
- smoke_test (N/N)
- 완료 이력 최근 5세션 (세션/의제 한 줄)

### 갱신 대상 외 (보존)
- STATUS 본문 나머지 (자동화 체인 설명, 과거 세션 완료 블록 등) — 수동 유지 영역
- 세션별 특수 블록 — 손대지 않음

### 가드레일
- TASKS.md → Notion 단방향
- 덮어쓰기 단위: SYNC_START/END 내부 전체 블록 교체 (append 금지 — 허위 이력 방지 원칙 유지)
- 제목 갱신 플래그: `--update-title` (기본 OFF, 세션 경계 호출만 ON)

### 불변 (세션86 합의 유지)
- `sync_from_finish()` wrapper 구조
- `sync_batch`/`_mark_done`/dedup 우회 (허위 이력 append 차단)
- Notion은 보조, Git이 기준 원본 ("TASKS.md > STATUS.md > HANDOFF.md > Notion")

## pass_ratio 집계
- GPT 조건부통과 (4묶음 수용 시 통과) → 채택 (조건부 단서가 설계 조건이므로 반영 시 해소)
- Gemini 통과 → 채택
- Claude 독립 설계 → 양측 검증 받음 (GPT의 기술적 보강 + Gemini의 전면 동의)
- pass_ratio = 3/3 = 1.0

## Round 1 종결 — 재라운드 불필요
6-5 조건부 생략 평가:
- 조건 A (양측 무단서 동의): GPT "조건부" 단서 있음 → 생략 불가
- 조건 C (의제 성격): B 분류 (notion_sync 구조 변경) → 6-5 유지 필수
- 결론: 6-5 수행. 본 종합안을 양측에 최종 검증 요청 후 구현 진행

## issue_class
B — notion_sync.py 구조 변경 (새 함수 추가 + API 경로 변경 + 신규 marker 블록)
